# Guía de Instalación Completa - DACDNS Agente

Guía paso a paso para instalar y configurar el agente DACDNS en una PC Windows desde cero.

---

## 📋 Requisitos Previos

- Windows 10/11
- Privilegios de Administrador
- Conexión a Internet

---

## 📦 PASO 1: Instalar Python

### 1.1 Descargar Python

1. Ve a: https://www.python.org/downloads/
2. Descarga **Python 3.11 o superior** (recomendado: 3.12+)
3. Ejecuta el instalador

### 1.2 Configurar instalación

✅ **IMPORTANTE:** En la primera pantalla del instalador:
- ☑️ Marca: **"Add Python to PATH"**
- Clic en **"Install Now"**

### 1.3 Verificar instalación

Abre PowerShell y verifica:

```powershell
python --version
```

Debería mostrar: `Python 3.12.x` o similar

---

## 📁 PASO 2: Preparar el Proyecto

### 2.1 Crear estructura de carpetas

```powershell
# Crear directorio del proyecto
New-Item -Path "D:\proyectos\dac\dacdns" -ItemType Directory -Force

# Ir al directorio
cd D:\proyectos\dac\dacdns
```

### 2.2 Copiar archivos del proyecto

Copia estos archivos a `D:\proyectos\dac\dacdns\`:

- `dacdns.py` (script principal)
- `iniciar_dacdns.bat` (script de inicio)
- `.env.example` (plantilla de configuración)

O descárgalos desde el repositorio/origen.

---

## 🐍 PASO 3: Crear Entorno Virtual

```powershell
# Estar en el directorio del proyecto
cd D:\proyectos\dac\dacdns

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1
```

**Nota:** Si da error de política de ejecución:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📦 PASO 4: Instalar Dependencias

```powershell
# Con el entorno virtual activado (.venv)
pip install paho-mqtt
```

Verifica que se instaló:

```powershell
pip list | Select-String paho
```

---

## ⚙️ PASO 5: Configurar Credenciales

### 5.1 Crear archivo .env

```powershell
# Copiar plantilla
Copy-Item .env.example .env
```

### 5.2 Editar .env con credenciales reales

```powershell
notepad .env
```

Contenido del archivo `.env`:

```env
MQTT_BROKER=98f1261f32ac495eb8a03d003a78b5b2.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=dacdns
MQTT_PASSWORD=TU_CONTRASEÑA_AQUI
UPDATE_INTERVAL=1800
```

**IMPORTANTE:** Reemplaza `TU_CONTRASEÑA_AQUI` con la contraseña real de MQTT.

Guarda y cierra el archivo.

---

## 🧪 PASO 6: Probar Manualmente

Antes de crear la tarea programada, prueba que funcione:

```powershell
.\iniciar_dacdns.bat
```

Deberías ver:

```
[INFO] Iniciando agente dacdns
[INFO] Hostname: NOMBRE-PC
[INFO] Conectado y autorizado en MQTT
[INFO] Publicando estado: {'hostname': 'NOMBRE-PC', 'ip': '192.168.x.x', ...}
```

**Si funciona correctamente, presiona `Ctrl+C` para detenerlo.**

---

## 🔧 PASO 7: Crear Tarea Programada

### 7.1 Abrir PowerShell como Administrador

1. Presiona `Win + X`
2. Selecciona **"Terminal (Administrador)"** o **"Windows PowerShell (Administrador)"**
3. Navega al proyecto:

```powershell
cd D:\proyectos\dac\dacdns
```

### 7.2 Ejecutar script de creación

```powershell
# Crear variables
$action = New-ScheduledTaskAction -Execute "D:\proyectos\dac\dacdns\iniciar_dacdns.bat" -WorkingDirectory "D:\proyectos\dac\dacdns"

$trigger = New-ScheduledTaskTrigger -AtStartup

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

# Registrar tarea
Register-ScheduledTask -TaskName "DACDNS_Agente" -Action $action -Trigger $trigger -Settings $settings -User "SYSTEM" -RunLevel Limited -Description "Agente DACDNS - Publica hostname e IP en MQTT"
```

Deberías ver:

```
TaskPath  TaskName        State
--------  --------        -----
\         DACDNS_Agente   Ready
```

---

## ✅ PASO 8: Verificar Funcionamiento

### 8.1 Iniciar la tarea manualmente

```powershell
Start-ScheduledTask -TaskName "DACDNS_Agente"
```

### 8.2 Verificar que está ejecutándose

```powershell
# Esperar 5 segundos
Start-Sleep -Seconds 5

# Ver procesos Python
Get-Process python | Select-Object Id, ProcessName, Path, StartTime
```

Deberías ver un proceso Python ejecutándose.

### 8.3 Ver estado de la tarea

```powershell
Get-ScheduledTaskInfo -TaskName "DACDNS_Agente" | Format-List LastRunTime, LastTaskResult, NextRunTime
```

### 8.4 Verificar en MQTT (Opcional)

Ve al Web Client de HiveMQ:
- URL: https://console.hivemq.cloud/
- Topic: `dac/pc/NOMBRE-PC`

Deberías ver el mensaje con el hostname e IP de la PC.

---

## 🔐 PASO 9: Proteger Credenciales (Opcional)

Restringir permisos del archivo `.env`:

```powershell
# Solo el usuario actual y SYSTEM pueden leer
icacls .env /inheritance:r
icacls .env /grant:r "$env:USERNAME`:F"
icacls .env /grant:r "SYSTEM:F"
```

---

## 🎯 Resumen de Comandos de Diagnóstico

### Ver estado de la tarea:

```powershell
Get-ScheduledTask -TaskName "DACDNS_Agente" | Format-List TaskName, State, LastRunTime
```

### Ver procesos Python activos:

```powershell
Get-Process python -ErrorAction SilentlyContinue | Format-Table Id, ProcessName, StartTime
```

### Detener la tarea:

```powershell
Stop-ScheduledTask -TaskName "DACDNS_Agente"
```

### Iniciar la tarea:

```powershell
Start-ScheduledTask -TaskName "DACDNS_Agente"
```

### Eliminar la tarea (si necesitas recrearla):

```powershell
Unregister-ScheduledTask -TaskName "DACDNS_Agente" -Confirm:$false
```

---

## 🚨 Solución de Problemas

### La tarea no se ejecuta

1. Verificar que el archivo `.bat` existe:
   ```powershell
   Test-Path "D:\proyectos\dac\dacdns\iniciar_dacdns.bat"
   ```

2. Verificar logs de Windows:
   ```powershell
   Get-WinEvent -LogName 'Microsoft-Windows-TaskScheduler/Operational' -MaxEvents 20 | 
       Where-Object { $_.Message -like "*DACDNS*" } | 
       Format-List TimeCreated, Message
   ```

3. Probar manualmente el `.bat`:
   ```powershell
   .\iniciar_dacdns.bat
   ```

### Error "ModuleNotFoundError: No module named 'paho'"

```powershell
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Reinstalar paho-mqtt
pip install paho-mqtt
```

### Error "Variables de entorno requeridas"

Verificar que el archivo `.env` existe y tiene las credenciales:

```powershell
Get-Content .env
```

### Python no encontrado

Reinstalar Python y asegurarse de marcar **"Add Python to PATH"**.

---

## 📝 Estructura Final del Proyecto

```
D:\proyectos\dac\dacdns\
├── .venv\                    # Entorno virtual (creado automáticamente)
├── dacdns.py                 # Script principal
├── iniciar_dacdns.bat        # Script de inicio
├── .env                      # Credenciales (NO subir a Git)
├── .env.example              # Plantilla de credenciales
├── README.md                 # Documentación
└── INSTALACION.md            # Este archivo
```

---

## ✅ Checklist Final

Antes de dar por completada la instalación, verifica:

- ☑️ Python instalado y en PATH
- ☑️ Entorno virtual creado (`.venv`)
- ☑️ Dependencia `paho-mqtt` instalada
- ☑️ Archivo `.env` configurado con credenciales correctas
- ☑️ Prueba manual funciona (`.\iniciar_dacdns.bat`)
- ☑️ Tarea programada creada
- ☑️ Tarea se ejecuta al iniciar manualmente
- ☑️ Proceso Python visible en `Get-Process python`
- ☑️ Mensaje llegando a MQTT (verificado en Web Client)

---

## 🎉 ¡Instalación Completada!

El agente DACDNS está ahora:
- ✅ Instalado y configurado
- ✅ Ejecutándose como tarea programada
- ✅ Se iniciará automáticamente con Windows
- ✅ Publicando hostname e IP cada 30 minutos

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa la sección **Solución de Problemas** arriba
2. Verifica los logs de la tarea programada
3. Prueba ejecutar manualmente `.\iniciar_dacdns.bat`
4. Verifica conectividad con el broker MQTT

---

**Fecha:** 8 de enero de 2026  
**Versión:** 1.0
