@echo off
REM Script para iniciar el cliente VPN (REQUIERE PRIVILEGIOS DE ADMINISTRADOR)

REM Verificar si se ejecuta como administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Este script requiere privilegios de administrador
    echo.
    echo Haga clic derecho en este archivo y seleccione "Ejecutar como administrador"
    echo.
    pause
    exit /b 1
)

REM Cambiar al directorio del script
cd /d "%~dp0"

REM Cargar variables de entorno desde archivo .env (si existe)
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        REM Ignorar líneas vacías y comentarios
        echo %%a | findstr /r /c:"^#" >nul || (
            if not "%%b"=="" set %%a=%%b
        )
    )
)

REM Ejecutar el programa Python con el entorno virtual
echo Iniciando cliente VPN...
echo.
"%~dp0.venv\Scripts\python.exe" "%~dp0cliente_vpn.py"

REM Si quieres que la ventana no se cierre en caso de error, descomenta la siguiente línea:
REM pause
