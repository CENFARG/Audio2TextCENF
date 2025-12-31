import json

launch_config = {
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Audio2Text Debug",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "justMyCode": False,
            "python": "${workspaceFolder}/.venv/Scripts/python.exe",
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}",
                "PYTHONUTF8": "1",
                "PYTHONIOENCODING": "utf-8"
            },
            "stopOnEntry": False,
            "showReturnValue": True,
            "redirectOutput": True
        },
        {
            "name": "Python: Debug CTkTabview (Step Into Libraries)",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "justMyCode": False,
            "python": "${workspaceFolder}/.venv/Scripts/python.exe",
            "cwd": "${workspaceFolder}",
            "stopOnEntry": False,
            "logToFile": True
        }
    ]
}

# Crear directorio si no existe
import os
os.makedirs('.vscode', exist_ok=True)

# Guardar archivo
with open('.vscode/launch.json', 'w', encoding='utf-8') as f:
    json.dump(launch_config, f, indent=4)

print("✅ launch.json creado exitosamente en .vscode/")
print("\nConfiguración:")
print("- justMyCode: False (permite step-into en librerías del venv)")
print("- Python: usa el intérprete del .venv")
print("\nAhora puedes:")
print("1. Poner un breakpoint en ui/app.py línea 102")
print("2. Presionar F5 o Run > Start Debugging")
print("3. Usar F11 (Step Into) para entrar en CTkTabview")
