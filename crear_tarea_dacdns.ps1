# Script para crear tarea programada de DACDNS (Agente LAN)
# Ejecutar como Administrador

Write-Host "Creando tarea programada para DACDNS Agente..." -ForegroundColor Cyan

# Configuración
$TaskName = "DACDNS_Agente"
$ScriptPath = "D:\proyectos\dac\dacdns\iniciar_dacdns.bat"
$WorkingDir = "D:\proyectos\dac\dacdns"

# Verificar que el script existe
if (-not (Test-Path $ScriptPath)) {
    Write-Host "ERROR: No se encuentra el archivo: $ScriptPath" -ForegroundColor Red
    exit 1
}

# Crear acción
$action = New-ScheduledTaskAction `
    -Execute $ScriptPath `
    -WorkingDirectory $WorkingDir

# Crear trigger (al iniciar el sistema)
$trigger = New-ScheduledTaskTrigger -AtStartup

# Configuración adicional
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# Usar cuenta SYSTEM para que funcione sin usuario logueado
$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Limited

Write-Host "Usuario configurado: SYSTEM" -ForegroundColor Yellow
Write-Host "Se ejecutara al iniciar Windows (sin usuario logueado)" -ForegroundColor Yellow
Write-Host ""

# Registrar tarea
try {
    # Eliminar tarea existente si existe
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
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
        -Description "Agente DACDNS - Publica hostname e IP en MQTT"
    
    Write-Host ""
    Write-Host "Tarea creada exitosamente: $TaskName" -ForegroundColor Green
    Write-Host ""
    Write-Host "Para probarla, ejecuta:" -ForegroundColor Cyan
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host ""
    Write-Host "Para ver el estado:" -ForegroundColor Cyan
    Write-Host "  Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo" -ForegroundColor White
    
} catch {
    Write-Host ""
    Write-Host "ERROR al crear la tarea:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
