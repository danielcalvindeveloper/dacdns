@echo off
REM Script para iniciar dacdns desde Tareas Programadas de Windows

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
"%~dp0.venv\Scripts\python.exe" "%~dp0dacdns.py"

REM Si quieres que la ventana no se cierre en caso de error, descomenta la siguiente línea:
REM pause
