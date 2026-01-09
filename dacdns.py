import socket
import time
import ssl
import json
import logging
import threading
import os
import sys
import signal
from datetime import datetime, timezone
from pathlib import Path
import paho.mqtt.client as mqtt

# ---------- LOG ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("dacdns")

# ---------- CONFIG ----------
BROKER = os.getenv("MQTT_BROKER", "98f1261f32ac495eb8a03d003a78b5b2.s1.eu.hivemq.cloud")
PORT = int(os.getenv("MQTT_PORT", "8883"))
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")
INTERVAL = int(os.getenv("UPDATE_INTERVAL", "60"))
MAX_RECONNECT_DELAY = 300  # 5 minutos máximo entre reintentos

# Validar credenciales
if not USERNAME or not PASSWORD:
    log.error("ERROR: Variables de entorno MQTT_USERNAME y MQTT_PASSWORD son requeridas")
    sys.exit(1)

hostname = socket.gethostname()
TOPIC = f"dac/pc/{hostname}"

# ---------- ESTADO GLOBAL ----------
current_timer = None
is_connected = False
is_running = True

# ---------- UTILS ----------
def get_ip():
    """Obtiene la IP del hostname con manejo de errores"""
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror as e:
        log.error(f"No se pudo resolver IP para {hostname}: {e}")
        return "unknown"
    except Exception as e:
        log.error(f"Error inesperado obteniendo IP: {e}")
        return "unknown"

def cancel_timer():
    """Cancela el timer actual si existe"""
    global current_timer
    if current_timer is not None:
        current_timer.cancel()
        current_timer = None
        log.debug("Timer cancelado")

def publish_status(client):
    """Publica el estado actual con manejo de errores"""
    global current_timer
    
    if not is_running:
        log.info("Deteniendo publicaciones (programa cerrándose)")
        return
    
    if not is_connected:
        log.warning("No conectado, saltando publicación")
        return
    
    try:
        ip = get_ip()
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = {
            "hostname": hostname,
            "ip": ip,
            "timestamp": timestamp
        }
        
        log.info(f"Publicando estado: {payload}")
        result = client.publish(TOPIC, json.dumps(payload), qos=1, retain=True)
        
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            log.error(f"Error al publicar: {mqtt.error_string(result.rc)}")
        
    except Exception as e:
        log.error(f"Error en publish_status: {e}", exc_info=True)
    finally:
        # Reprograma el próximo envío solo si seguimos conectados
        if is_connected and is_running:
            current_timer = threading.Timer(INTERVAL, publish_status, args=(client,))
            current_timer.start()

# ---------- CALLBACKS ----------
def on_connect(client, userdata, flags, reason_code, properties=None):
    """Callback cuando se conecta al broker"""
    global is_connected
    
    if reason_code == 0:
        log.info("✓ Conectado y autorizado en MQTT")
        is_connected = True
        publish_status(client)
    else:
        log.error(f"✗ Conexión rechazada (rc={reason_code})")
        is_connected = False

def on_disconnect(client, userdata, reason_code, properties=None):
    """Callback cuando se desconecta del broker (firma corregida para VERSION2)"""
    global is_connected
    
    is_connected = False
    cancel_timer()
    
    if reason_code == 0:
        log.info("Desconectado limpiamente del broker")
    else:
        log.warning(f"Desconectado del broker (rc={reason_code}), reintentando...")

def signal_handler(signum, frame):
    """Maneja señales de sistema para salida limpia"""
    global is_running
    
    log.info(f"Señal {signum} recibida, cerrando limpiamente...")
    is_running = False
    cancel_timer()
    
    if client:
        try:
            client.disconnect()
            client.loop_stop()
        except:
            pass
    
    sys.exit(0)

# ---------- MQTT CLIENT ----------
client = mqtt.Client(
    client_id="",
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)

client.username_pw_set(USERNAME, PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)

client.on_connect = on_connect
client.on_disconnect = on_disconnect

# Configurar reconexión automática
client.reconnect_delay_set(min_delay=1, max_delay=MAX_RECONNECT_DELAY)

# ---------- SIGNAL HANDLERS ----------
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Kill

# ---------- MAIN ----------
log.info("Iniciando agente dacdns")
log.info(f"Hostname: {hostname}")
log.info(f"Topic: {TOPIC}")
log.info(f"Broker: {BROKER}:{PORT}")
log.info(f"Intervalo de actualización: {INTERVAL}s")

# Intentar conectar con manejo de errores
try:
    log.info("Conectando al broker MQTT...")
    client.connect(BROKER, PORT, keepalive=60)
    
    # Loop forever con reconexión automática
    client.loop_forever(retry_first_connection=True)
    
except KeyboardInterrupt:
    log.info("Interrupción de teclado detectada")
    signal_handler(signal.SIGINT, None)
    
except Exception as e:
    log.error(f"Error fatal: {e}", exc_info=True)
    sys.exit(1)
    
finally:
    log.info("Agente dacdns finalizado")
    cancel_timer()
