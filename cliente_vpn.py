import socket
import ssl
import json
import logging
import os
import sys
import signal
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
import paho.mqtt.client as mqtt

# ---------- LOG ----------
logging.basicConfig(
    level=logging.INFO,  # INFO en producción, DEBUG solo para troubleshooting
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("cliente_vpn")

# ---------- CONFIG ----------
BROKER = os.getenv("MQTT_BROKER", "98f1261f32ac495eb8a03d003a78b5b2.s1.eu.hivemq.cloud")
PORT = int(os.getenv("MQTT_PORT", "8883"))
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")
HOSTS_FILE = Path(r"C:\Windows\System32\drivers\etc\hosts")
UPDATE_INTERVAL = int(os.getenv("HOSTS_UPDATE_INTERVAL", "30"))  # segundos
TTL_MINUTES = int(os.getenv("HOST_TTL_MINUTES", "5"))  # minutos antes de considerar host inactivo
IGNORE_LOCAL_HOST = os.getenv("IGNORE_LOCAL_HOST", "true").lower() == "true"  # Ignorar hostname local

# Marcadores del bloque en hosts
BEGIN_MARKER = "# --- BEGIN MQTT-HOSTS ---"
END_MARKER = "# --- END MQTT-HOSTS ---"

# Validar credenciales
if not USERNAME or not PASSWORD:
    log.error("ERROR: Variables de entorno MQTT_USERNAME y MQTT_PASSWORD son requeridas")
    sys.exit(1)

# Obtener hostname local
local_hostname = socket.gethostname()

# ---------- ESTADO GLOBAL ----------
hosts_map = {}  # {hostname: {"ip": "x.x.x.x", "timestamp": datetime}}
is_running = True
pending_update = False

# ---------- UTILIDADES ----------

def check_admin():
    """Verifica si el script se ejecuta con privilegios de administrador"""
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if not is_admin:
            log.error("ERROR: Este script requiere privilegios de administrador")
            log.error("Ejecute PowerShell como Administrador y vuelva a intentar")
            sys.exit(1)
    except Exception as e:
        log.warning(f"No se pudo verificar privilegios de administrador: {e}")

def parse_timestamp(ts_str):
    """Convierte timestamp ISO 8601 a datetime"""
    try:
        # Manejar tanto con +00:00 como con Z
        if ts_str.endswith('Z'):
            ts_str = ts_str[:-1] + '+00:00'
        return datetime.fromisoformat(ts_str)
    except Exception as e:
        log.error(f"Error parseando timestamp '{ts_str}': {e}")
        return datetime.now(timezone.utc)

def is_host_active(timestamp):
    """Determina si un host está activo basado en su timestamp"""
    now = datetime.now(timezone.utc)
    age = now - timestamp
    return age < timedelta(minutes=TTL_MINUTES)

def update_hosts_file():
    """Actualiza el archivo hosts con escritura atómica"""
    global pending_update
    
    if not pending_update:
        return
    
    try:
        log.info(f"Actualizando archivo hosts: {HOSTS_FILE}")
        
        # Leer archivo actual
        if HOSTS_FILE.exists():
            with open(HOSTS_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Encontrar y remover bloque existente
        new_lines = []
        in_block = False
        
        for line in lines:
            if BEGIN_MARKER in line:
                in_block = True
                continue
            if END_MARKER in line:
                in_block = False
                continue
            if not in_block:
                new_lines.append(line)
        
        # Construir nuevo bloque
        block_lines = [BEGIN_MARKER + "\n"]
        
        active_count = 0
        inactive_count = 0
        
        for hostname, data in sorted(hosts_map.items()):
            ip = data["ip"]
            timestamp = data["timestamp"]
            
            if is_host_active(timestamp):
                block_lines.append(f"{ip:<15}   {hostname}\n")
                active_count += 1
            else:
                # Comentar hosts inactivos
                block_lines.append(f"# {ip:<15}   {hostname}  # Inactivo desde {timestamp.isoformat()}\n")
                inactive_count += 1
        
        block_lines.append(END_MARKER + "\n")
        
        # Insertar bloque al final
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines.append('\n')
        
        new_lines.extend(block_lines)
        
        # Escribir de forma atómica
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, 
                                         dir=HOSTS_FILE.parent, suffix='.tmp') as tmp_file:
            tmp_file.writelines(new_lines)
            tmp_path = Path(tmp_file.name)
        
        # Reemplazar archivo original
        shutil.move(str(tmp_path), str(HOSTS_FILE))
        
        log.info(f"✓ Hosts actualizado: {active_count} activos, {inactive_count} inactivos")
        pending_update = False
        
    except PermissionError:
        log.error("ERROR: Sin permisos para escribir en hosts. Ejecute como Administrador")
    except Exception as e:
        log.error(f"Error actualizando hosts: {e}", exc_info=True)

# ---------- CALLBACKS MQTT ----------

def on_connect(client, userdata, flags, reason_code, properties=None):
    """Callback cuando se conecta al broker"""
    if reason_code == 0:
        log.info("✓ Conectado al broker MQTT")
        
        # Suscribirse a todos los hosts
        topic = "dac/pc/#"
        client.subscribe(topic, qos=1)
        log.info(f"✓ Suscrito a topic: {topic}")
        
    else:
        log.error(f"✗ Conexión rechazada (rc={reason_code})")

def on_disconnect(client, userdata, reason_code, properties=None):
    """Callback cuando se desconecta del broker"""
    if reason_code == 0:
        log.info("Desconectado limpiamente del broker")
    else:
        log.warning(f"Desconectado del broker (rc={reason_code}), reintentando...")

def on_message(client, userdata, msg):
    """Callback cuando se recibe un mensaje"""
    global pending_update
    
    log.debug(f"📨 Mensaje recibido en topic: {msg.topic}")
    
    try:
        # Parsear topic: dac/pc/{hostname}
        topic_parts = msg.topic.split('/')
        if len(topic_parts) != 3:
            log.warning(f"Topic inesperado: {msg.topic}")
            return
        
        hostname = topic_parts[2]
        log.debug(f"Hostname extraído: {hostname}")
        
        # Ignorar hostname local si está configurado
        if IGNORE_LOCAL_HOST and hostname.upper() == local_hostname.upper():
            log.debug(f"Ignorando host local: {hostname}")
            return
        
        # Parsear payload
        payload_raw = msg.payload.decode('utf-8')
        log.debug(f"Payload recibido de {hostname}: {payload_raw}")
        
        payload = json.loads(payload_raw)
        
        ip = payload.get("ip")
        timestamp_str = payload.get("timestamp")
        
        if not ip or not timestamp_str:
            log.warning(f"Payload incompleto de {hostname}: {payload}")
            return
        
        # Ignorar IPs desconocidas
        if ip == "unknown":
            log.debug(f"Ignorando IP 'unknown' de {hostname}")
            return
        
        timestamp = parse_timestamp(timestamp_str)
        
        # Actualizar mapa
        if hostname in hosts_map:
            old_ip = hosts_map[hostname]["ip"]
            if old_ip != ip:
                log.info(f"📍 {hostname}: {old_ip} → {ip}")
            else:
                log.debug(f"♻️  {hostname}: {ip} (actualización)")
        else:
            log.info(f"➕ Nuevo host: {hostname} = {ip}")
        
        hosts_map[hostname] = {
            "ip": ip,
            "timestamp": timestamp
        }
        
        pending_update = True
        
    except json.JSONDecodeError as e:
        log.warning(f"Mensaje ignorado (no es JSON válido) del topic {msg.topic}")
        log.warning(f"Payload raw: {msg.payload[:200]}")  # Primeros 200 bytes
        log.warning(f"Sugerencia: Eliminar este mensaje retenido del broker")
    except Exception as e:
        log.error(f"Error procesando mensaje: {e}", exc_info=True)

def on_subscribe(client, userdata, mid, reason_code_list, properties=None):
    """Callback cuando se completa la suscripción"""
    log.info("✓ Suscripción confirmada")

# ---------- SIGNAL HANDLERS ----------

def signal_handler(signum, frame):
    """Maneja señales de sistema para salida limpia"""
    global is_running
    
    log.info(f"Señal {signum} recibida, cerrando limpiamente...")
    is_running = False
    
    # Actualización final
    if pending_update:
        update_hosts_file()
    
    if client:
        try:
            client.disconnect()
            client.loop_stop()
        except:
            pass
    
    sys.exit(0)

# ---------- MAIN ----------

def main():
    global client
    
    log.info("=" * 60)
    log.info("Cliente VPN - Actualizador Automático de Hosts")
    log.info("=" * 60)
    
    # Verificar privilegios de administrador
    check_admin()
    log.info(f"Hostname local: {local_hostname}")
    log.info(f"Ignorar host local: {'Sí' if IGNORE_LOCAL_HOST else 'No'}")
    
    log.info(f"Archivo hosts: {HOSTS_FILE}")
    log.info(f"Broker MQTT: {BROKER}:{PORT}")
    log.info(f"Intervalo de actualización: {UPDATE_INTERVAL}s")
    log.info(f"TTL de hosts: {TTL_MINUTES} minutos")
    
    # Configurar cliente MQTT
    client = mqtt.Client(
        client_id="vpn_client",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    
    client.username_pw_set(USERNAME, PASSWORD)
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_subscribe = on_subscribe
    
    # Configurar reconexión automática
    client.reconnect_delay_set(min_delay=1, max_delay=300)
    
    # Signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Conectar
    try:
        log.info("Conectando al broker MQTT...")
        client.connect(BROKER, PORT, keepalive=60)
        
        # Iniciar loop en background
        client.loop_start()
        
        log.info("✓ Cliente iniciado correctamente")
        log.info("Esperando mensajes MQTT...")
        
        # Loop principal: actualizar hosts periódicamente
        import time
        last_update = 0
        
        while is_running:
            time.sleep(1)
            
            now = time.time()
            if pending_update and (now - last_update) >= UPDATE_INTERVAL:
                update_hosts_file()
                last_update = now
        
    except KeyboardInterrupt:
        log.info("Interrupción de teclado detectada")
        signal_handler(signal.SIGINT, None)
        
    except Exception as e:
        log.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)
        
    finally:
        log.info("Cliente VPN finalizado")

if __name__ == "__main__":
    main()
