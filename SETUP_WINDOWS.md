# Crear y usar el entorno en Windows

Pasos rápidos para crear el entorno virtual e instalar dependencias (desde este directorio):

1. Ejecutar el script (PowerShell) que ya está en el repo:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\env_setup.ps1
```

2. Activar el entorno en futuras sesiones:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Ejecutar el agente:

```powershell
.\.venv\Scripts\python.exe dacdns.py
```

Notas:
- `requirements.txt` contiene `paho-mqtt`.
- Si prefieres crear el venv manualmente:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Ejecuta `iniciar_dacdns.bat` como Administrador para probar desde la tarea programada.
