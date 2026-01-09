# Script para crear tarea programada del Cliente VPN con cuenta SYSTEM
# Debe ejecutarse como Administrador

param(
    [string]$WorkingDir = "C:\proyectos\dac\dacdns",
    [string]$TaskName = "ClienteVPN_Hosts"
)

Write-Host "Creando tarea programada: $TaskName" -ForegroundColor Green
Write-Host "Directorio de trabajo: $WorkingDir" -ForegroundColor Cyan

# Verificar que el archivo .bat existe
$batPath = Join-Path $WorkingDir "iniciar_cliente_vpn.bat"
if (-not (Test-Path $batPath)) {
    Write-Host "ERROR: No se encuentra el archivo $batPath" -ForegroundColor Red
    exit 1
}

# Verificar que el archivo .env existe
$envPath = Join-Path $WorkingDir ".env"
if (-not (Test-Path $envPath)) {
    Write-Host "ADVERTENCIA: No se encuentra el archivo .env en $WorkingDir" -ForegroundColor Yellow
    Write-Host "Asegurese de que existe antes de ejecutar la tarea" -ForegroundColor Yellow
}

# Definir la acción (ejecutar el .bat)
$action = New-ScheduledTaskAction `
    -Execute $batPath `
    -WorkingDirectory $WorkingDir

# Definir el trigger (al iniciar el sistema)
$trigger = New-ScheduledTaskTrigger -AtStartup

# Definir el principal (cuenta SYSTEM con privilegios más altos)
$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Configuración adicional
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 0)  # Sin limite de tiempo

# Descripcion de la tarea
$description = "Cliente VPN - Actualiza automaticamente el archivo hosts con IPs de equipos publicadas en MQTT. Ejecuta como SYSTEM para tener permisos de escritura en hosts."

# Registrar la tarea
try {
    # Eliminar tarea existente si existe
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Eliminando tarea existente..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    # Crear nueva tarea
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description $description | Out-Null

    Write-Host ""
    Write-Host "Tarea programada creada exitosamente" -ForegroundColor Green
    Write-Host ""
    Write-Host "Detalles de la tarea:" -ForegroundColor Cyan
    Write-Host "  Nombre: $TaskName"
    Write-Host "  Usuario: SYSTEM"
    Write-Host "  Ejecutar: $batPath"
    Write-Host "  Directorio: $WorkingDir"
    Write-Host "  Trigger: Al inicio del sistema"
    Write-Host "  Reintentos: 3 veces cada 1 minuto si falla"
    Write-Host ""
    Write-Host "Para probar la tarea manualmente:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
    Write-Host "Para ver el estado de la tarea:" -ForegroundColor Yellow
    Write-Host "  Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo"
    Write-Host ""
    Write-Host "Para ver logs (Event Viewer):" -ForegroundColor Yellow
    Write-Host "  Programador de tareas -> Historial de la tarea"
    Write-Host ""

} catch {
    Write-Host "ERROR al crear la tarea: $_" -ForegroundColor Red
    exit 1
}
