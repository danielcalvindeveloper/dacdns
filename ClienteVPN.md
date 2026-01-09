Resolución de nombres en VPN QNAP usando MQTT + hosts dinámico
1. Problema

En entornos con QNAP QVPN, la conectividad IP funciona correctamente, pero la resolución de nombres (hostname → IP) no está garantizada:

No hay DNS interno confiable expuesto por la VPN

No se propagan broadcasts (NetBIOS / mDNS)

Acceso por IP funciona, por nombre no

Esto impacta directamente en:

Escritorio remoto (RDP)

Acceso a recursos compartidos

Scripts y herramientas que dependen de hostnames

2. Restricciones del entorno

❌ No es posible instalar WireGuard

❌ No se puede modificar el comportamiento interno de QVPN

✅ Existe un broker MQTT accesible (HiveMQ)

✅ Cada PC de la LAN ejecuta un agente que conoce su hostname e IP

✅ El cliente VPN es Windows

3. Enfoque adoptado (criterio)

Se implementa una resolución de nombres distribuida, basada en:

MQTT como canal de estado

Mensajes retenidos (retain)

Archivo hosts administrado automáticamente en el cliente VPN

👉 Se evita forzar DNS, WINS o mecanismos que QVPN no soporta bien.
👉 Se privilegia determinismo y control sobre “descubrimiento mágico”.

4. Arquitectura general

Componentes:

Agente LAN (por PC interna)

Publica hostname + IP por MQTT

Actualiza periódicamente (heartbeat)

Broker MQTT (HiveMQ)

Retiene el último mensaje por host

Cliente VPN (Windows)

Se subscribe a los topics

Mantiene actualizado un bloque del archivo hosts

5. Diseño de topics MQTT
Un topic por host
dac/pc/{hostname}


Ejemplo:

dac/pc/DYD01

Payload (estado actual)
{
  "hostname": "DYD01",
  "ip": "192.168.1.41",
  "timestamp": "2026-01-08T18:03:40Z"
}

Características del mensaje

retain = true

QoS 0 o 1

Se sobrescribe siempre el estado anterior

📌 Clave:
Un cliente nuevo recibe solo el último mensaje de cada host, no el histórico.

6. Comportamiento del cliente VPN
Suscripción
dac/pc/#


Al conectarse:

Recibe un snapshot completo del estado actual de la red

No procesa backlog

No depende del orden de llegada

7. Gestión del archivo hosts
Principio fundamental

👉 Nunca modificar el archivo completo
👉 Mantener un bloque claramente delimitado

Ejemplo:

# --- BEGIN MQTT-HOSTS ---
192.168.1.41   DYD01
192.168.1.20   NAS
# --- END MQTT-HOSTS ---


Todo lo externo al bloque queda intacto

El bloque es idempotente

Puede regenerarse completamente en cada ciclo

8. Estrategia de actualización

Mantener en memoria un mapa {hostname → ip, timestamp}

Reescribir el bloque:

al recibir cambios

o en intervalos controlados (ej. 30–60s)

Escritura atómica:

archivo temporal

replace final

⚠️ El proceso debe ejecutarse con privilegios de administrador.

9. Manejo de hosts inactivos
Estrategia recomendada (TTL lógico)

Si now - timestamp > N minutos:

comentar o remover la entrada del bloque

Ejemplo:

#192.168.1.50   PC-VIEJA


No se borra el retained message:
se decide en el cliente qué está “vigente”.

10. Ventajas de la solución

✔ No depende de QVPN

✔ No requiere DNS interno

✔ Funciona con RDP, SMB, scripts, etc.

✔ Escala bien en redes chicas/medianas

✔ MQTT ya está disponible

✔ Estado determinístico (no descubrimiento heurístico)

11. Riesgos y mitigaciones
Riesgo	Mitigación
Broker MQTT caído	Último hosts queda operativo
Script detenido	Servicio / tarea programada
IP incorrecta	Timestamp + TTL
Escritura concurrente	Bloque exclusivo
12. Conclusión

Esta solución no es un workaround, es un patrón válido de infraestructura liviana:

Usa MQTT como fuente de verdad del estado

Evita forzar herramientas que la VPN no soporta bien

Resuelve el problema real: “quiero conectarme por nombre”

Es especialmente adecuada cuando:

No se puede instalar WireGuard

No hay control sobre la VPN

Se prioriza previsibilidad y control