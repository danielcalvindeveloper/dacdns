# Instalación de DACDNS como Tarea Programada de Windows

## 1. Configurar las credenciales

Crea un archivo `.env` en este directorio con tus credenciales:

```bash
MQTT_BROKER=98f1261f32ac495eb8a03d003a78b5b2.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=dacdns
MQTT_PASSWORD=04077888Hq
UPDATE_INTERVAL=60
```

**IMPORTANTE:** Este archivo `.env` NO se subirá a Git (está en `.gitignore`)

## 2. Verificar que funciona

Ejecuta manualmente el script:
```cmd
iniciar_dacdns.bat
```

Deberías ver:
```
[INFO] Iniciando agente dacdns
[INFO] Conectado y autorizado en MQTT
[INFO] Publicando estado: {'hostname': '...', 'ip': '...'}
```

## 3. Crear la Tarea Programada

### Opción A: Mediante PowerShell (Recomendado)

Ejecuta como **Administrador** en PowerShell:

```powershell
$action = New-ScheduledTaskAction -Execute "D:\proyectos\dac\dacdns\iniciar_dacdns.bat" -WorkingDirectory "D:\proyectos\dac\dacdns"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "TU_USUARIO" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName "DACDNS" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Agente DACDNS para actualización de IP"
```

**Reemplaza `TU_USUARIO`** con el usuario específico que creaste.

### Opción B: Mediante Interfaz Gráfica

1. Presiona `Win + R` y escribe `taskschd.msc`
2. Clic en "Crear tarea..."
3. **General:**
   - Nombre: `DACDNS`
   - Usuario: Selecciona tu usuario específico
   - ✅ Ejecutar con los privilegios más altos
   - ✅ Ejecutar aunque el usuario no haya iniciado sesión
4. **Desencadenadores:**
   - Nuevo → Al iniciar el sistema
5. **Acciones:**
   - Programa: `D:\proyectos\dac\dacdns\iniciar_dacdns.bat`
   - Iniciar en: `D:\proyectos\dac\dacdns`
6. **Configuración:**
   - ✅ Permitir que la tarea se ejecute a petición
   - ✅ Ejecutar la tarea lo antes posible si se perdió un inicio programado
   - Si la tarea falla, reiniciar cada: `1 minuto`, Intentar reiniciar hasta: `3 veces`

## 4. Probar la Tarea

En el Programador de tareas:
- Busca la tarea `DACDNS`
- Clic derecho → "Ejecutar"
- Verifica que se ejecute correctamente

## 5. Configurar permisos del archivo .env

Para mayor seguridad, restringe los permisos del archivo `.env`:

```powershell
icacls .env /inheritance:r
icacls .env /grant:r "%USERNAME%:F"
icacls .env /grant:r "SYSTEM:F"
```

## Solución de problemas

### La tarea no inicia
- Verifica que el archivo `.env` exista y tenga las credenciales correctas
- Revisa los logs en el Programador de tareas (pestaña "Historial")
- Verifica que el usuario tenga permisos de lectura en el directorio

### Error de conexión MQTT
- Ejecuta `iniciar_dacdns.bat` manualmente para ver el error completo
- Verifica las credenciales en `.env`
- Comprueba la conectividad de red

### El programa se detiene
- Revisa los logs de la tarea programada
- Verifica que el entorno virtual (`.venv`) esté intacto
