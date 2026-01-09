# Script completo para configurar DACDNS con usuario dedicado
# Ejecutar como Administrador

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Configuracion Segura de DACDNS con Usuario Dedicado" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Configuración
$Username = "svc_dacdns"
$Password = "DacDNS_2026_Secure!" # Cambiar por una más segura si quieres
$ProjectPath = "D:\proyectos\dac\dacdns"
$TaskName = "DACDNS_Agente"

# ========================================
# PASO 1: Crear usuario dedicado
# ========================================
Write-Host "[1/4] Creando usuario dedicado '$Username'..." -ForegroundColor Yellow

try {
    # Verificar si el usuario ya existe
    $existingUser = Get-LocalUser -Name $Username -ErrorAction SilentlyContinue
    
    if ($existingUser) {
        Write-Host "  Usuario ya existe. Eliminando para recrear..." -ForegroundColor Gray
        Remove-LocalUser -Name $Username -ErrorAction Stop
    }
    
    # Crear usuario
    $SecurePassword = ConvertTo-SecureString $Password -AsPlainText -Force
    New-LocalUser -Name $Username `
        -Password $SecurePassword `
        -Description "Servicio DACDNS - Usuario de privilegios minimos" `
        -PasswordNeverExpires `
        -UserMayNotChangePassword `
        -ErrorAction Stop | Out-Null
    
    Write-Host "  Usuario '$Username' creado correctamente" -ForegroundColor Green
    
} catch {
    Write-Host "  ERROR: No se pudo crear el usuario" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    exit 1
}

# ========================================
# PASO 2: Configurar permisos del proyecto
# ========================================
Write-Host ""
Write-Host "[2/4] Configurando permisos en '$ProjectPath'..." -ForegroundColor Yellow

try {
    # Dar permisos de lectura y ejecución al directorio del proyecto
    icacls "$ProjectPath" /grant "${Username}:(OI)(CI)RX" /T /Q | Out-Null
    
    Write-Host "  Permisos de lectura/ejecucion configurados" -ForegroundColor Green
    
} catch {
    Write-Host "  ERROR: No se pudieron configurar permisos" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    exit 1
}

# ========================================
# PASO 3: Crear tarea programada
# ========================================
Write-Host ""
Write-Host "[3/4] Creando tarea programada..." -ForegroundColor Yellow

try {
    # Eliminar tarea existente si existe
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Write-Host "  Eliminando tarea existente..." -ForegroundColor Gray
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Crear acción
    $action = New-ScheduledTaskAction `
        -Execute "$ProjectPath\iniciar_dacdns.bat" `
        -WorkingDirectory $ProjectPath
    
    # Crear trigger (al iniciar el sistema)
    $trigger = New-ScheduledTaskTrigger -AtStartup
    
    # Configuración adicional
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1)
    
    # Crear principal (usuario dedicado)
    $principal = New-ScheduledTaskPrincipal `
        -UserId $Username `
        -LogonType Password `
        -RunLevel Limited
    
    # Registrar tarea con contraseña
    $SecurePasswordForTask = ConvertTo-SecureString $Password -AsPlainText -Force
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Agente DACDNS - Publica hostname e IP en MQTT (usuario: $Username)" `
        -User $Username `
        -Password (New-Object System.Management.Automation.PSCredential($Username, $SecurePasswordForTask)).GetNetworkCredential().Password `
        -ErrorAction Stop | Out-Null
    
    Write-Host "  Tarea programada creada correctamente" -ForegroundColor Green
    
} catch {
    Write-Host "  ERROR: No se pudo crear la tarea programada" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    exit 1
}

# ========================================
# PASO 4: Verificar configuración
# ========================================
Write-Host ""
Write-Host "[4/4] Verificando configuracion..." -ForegroundColor Yellow

try {
    $task = Get-ScheduledTask -TaskName $TaskName
    $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
    
    Write-Host "  Tarea: $($task.TaskName)" -ForegroundColor Green
    Write-Host "  Estado: $($task.State)" -ForegroundColor Green
    Write-Host "  Usuario: $($task.Principal.UserId)" -ForegroundColor Green
    Write-Host "  Ultima ejecucion: $($taskInfo.LastRunTime)" -ForegroundColor Green
    
} catch {
    Write-Host "  ERROR: No se pudo verificar la tarea" -ForegroundColor Red
}

# ========================================
# RESUMEN
# ========================================
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Configuracion Completada" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Usuario creado:" -ForegroundColor White
Write-Host "  Nombre: $Username" -ForegroundColor Gray
Write-Host "  Contrasena: $Password" -ForegroundColor Gray
Write-Host "  Privilegios: Minimos (solo lectura del proyecto)" -ForegroundColor Gray
Write-Host ""
Write-Host "La tarea se ejecutara automaticamente al iniciar Windows" -ForegroundColor White
Write-Host ""
Write-Host "Comandos utiles:" -ForegroundColor Yellow
Write-Host "  Probar tarea ahora:" -ForegroundColor White
Write-Host "    Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host ""
Write-Host "  Ver estado:" -ForegroundColor White
Write-Host "    Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo" -ForegroundColor Gray
Write-Host ""
Write-Host "  Ver logs (si falla):" -ForegroundColor White
Write-Host "    Get-WinEvent -LogName 'Microsoft-Windows-TaskScheduler/Operational' -MaxEvents 10" -ForegroundColor Gray
Write-Host ""
Write-Host "IMPORTANTE: Guarda la contrasena del usuario en un lugar seguro" -ForegroundColor Yellow
Write-Host ""
