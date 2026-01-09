# Script para crear/activar entorno virtual e instalar dependencias en Windows (PowerShell)
param(
    [string]$venvName = ".venv"
)

Write-Host "Creando entorno virtual '$venvName'..."
python -m venv $venvName

Write-Host "Activando entorno virtual..."
# Activar el venv en la sesión actual
& "$PWD\$venvName\Scripts\Activate.ps1"

Write-Host "Actualizando pip e instalando dependencias desde requirements.txt..."
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Entorno listo. Para activar en futuras sesiones (PowerShell):"
Write-Host "    .\$venvName\Scripts\Activate.ps1"
Write-Host "Para ejecutar el agente: .\$venvName\Scripts\python.exe dacdns.py"
