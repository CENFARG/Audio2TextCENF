# 🧪 Guía de Verificación - Audio2Text v0.9.2

Esta guía verifica que cualquier persona pueda clonar, instalar, ejecutar y compilar el proyecto sin problemas.

---

## ✅ Checklist de Verificación Completa

### 1. Clonar el Repositorio

```bash
# Clonar
git clone https://github.com/CENFARG/Audio2Text.git
cd Audio2Text

# Verificar estructura
dir  # Windows
# o
ls   # Linux/Mac
```

**Debe mostrar:**
```
assets/
backend/
config/
docs/
lang/
scripts/
templates/
ui/
main.py
requirements.txt
setup.py
pyproject.toml
README.md
...
```

✅ **Verificado:** Estructura completa presente

---

### 2. Crear Entorno Virtual

```bash
# Crear entorno virtual
python -m venv .venv

# Verificar que se creó
dir .venv  # Debe existir
```

✅ **Verificado:** Entorno virtual creado

---

### 3. Activar Entorno Virtual

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

**Verificar activación:**
```bash
python --version  # Debe mostrar Python 3.8+
which python      # Debe apuntar a .venv
```

✅ **Verificado:** Entorno activado correctamente

---

### 4. Instalar Dependencias

```bash
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

**Verificar instalación:**
```bash
pip list
```

**Debe incluir:**
- customtkinter
- groq
- sounddevice
- Pillow
- pyinstaller
- (y todas las demás del requirements.txt)

✅ **Verificado:** Todas las dependencias instaladas

---

### 5. Configurar API Key (Temporal para Testing)

Crea un archivo `config/config.json` temporal:

```json
{
    "groq_api_key": "TU_API_KEY_AQUI",
    "default_language": "es",
    "hotkey": "F2",
    "audio_path": "audio",
    "logs_path": "logs",
    "max_audio_size_mb": 100,
    "max_log_size_mb": 50
}
```

**NOTA:** Este archivo NO se sube a Git (está en .gitignore)

✅ **Verificado:** Configuración creada

---

### 6. Ejecutar desde Código Fuente

```bash
python main.py
```

**Debe:**
- ✅ Abrir la ventana de Audio2Text
- ✅ Mostrar las 3 pestañas (Principal, Configuración, Información)
- ✅ Permitir configurar la API key
- ✅ Permitir grabar audio (con API key válida)

**Verificar logs:**
```bash
dir logs  # Debe haber un archivo app_YYYYMMDD_HHMMSS.log
```

✅ **Verificado:** Aplicación ejecuta correctamente

---

### 7. Compilar Ejecutable (Variante GENERAL)

```bash
# Compilar variante GENERAL
python scripts/build_GENERAL_v2.py
```

**Proceso esperado:**
```
🔨 Compilando Audio2Text CENF 0.9.2 - Variante: GENERAL
📋 Verificando dependencias...
✅ PyInstaller encontrado
🧹 Limpiando builds anteriores...
🏗️  Ejecutando PyInstaller...
...
✅ Build completado exitosamente!
📦 Ejecutable: dist\Audio2Text_CENF_0.9.2_GENERAL.exe
```

**Verificar:**
```bash
dir dist  # Debe existir Audio2Text_CENF_0.9.2_GENERAL.exe
```

✅ **Verificado:** Compilación exitosa

---

### 8. Probar Ejecutable Compilado

```bash
# Ejecutar el .exe
.\dist\Audio2Text_CENF_0.9.2_GENERAL.exe
```

**Debe:**
- ✅ Abrir sin errores
- ✅ Funcionar igual que desde código fuente
- ✅ Crear config.json si no existe
- ✅ Crear carpetas audio/ y logs/

✅ **Verificado:** Ejecutable funciona correctamente

---

### 9. Compilar Todas las Variantes

```bash
# Compilar las 3 variantes
python scripts/build_all_v2.py
```

**Debe generar:**
```
dist/
├── Audio2Text_CENF_0.9.2_GENERAL.exe
├── Audio2Text_CENF_0.9.2_CONTRERAS.exe
└── Audio2Text_CENF_0.9.2_CUTIGNOLA.exe
```

**Verificar tamaños:**
```bash
dir dist\*.exe
```

Cada .exe debe tener ~80-120 MB aproximadamente.

✅ **Verificado:** Todas las variantes compiladas

---

### 10. Verificar Build Artifacts

```bash
dir _build_artifacts
```

**Debe contener:**
```
_build_artifacts/
├── build/
│   ├── GENERAL/
│   ├── CONTRERAS/
│   └── CUTIGNOLA/
├── logs/
│   ├── GENERAL/
│   ├── CONTRERAS/
│   └── CUTIGNOLA/
└── specs/
    ├── GENERAL/
    ├── CONTRERAS/
    └── CUTIGNOLA/
```

✅ **Verificado:** Artifacts organizados correctamente

---

## 🐛 Problemas Comunes y Soluciones

### Problema 1: "python no se reconoce"

**Solución:**
```bash
# Verificar instalación de Python
python --version

# Si no funciona, agregar Python al PATH
# O usar:
py --version  # Windows
python3 --version  # Linux/Mac
```

### Problema 2: "No module named 'customtkinter'"

**Solución:**
```bash
# Verificar que el entorno virtual está activado
# Debe aparecer (.venv) al inicio del prompt

# Reinstalar dependencias
pip install -r requirements.txt
```

### Problema 3: "Permission denied" al activar .venv

**Solución (Windows PowerShell):**
```powershell
# Ejecutar como administrador
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Luego activar
.venv\Scripts\Activate.ps1
```

### Problema 4: Error al compilar con PyInstaller

**Solución:**
```bash
# Limpiar builds anteriores
python scripts/cleanup_build_artifacts.py

# Reinstalar PyInstaller
pip uninstall pyinstaller
pip install pyinstaller>=6.0.0

# Intentar de nuevo
python scripts/build_GENERAL_v2.py
```

### Problema 5: "ModuleNotFoundError: No module named 'backend'"

**Solución:**
```bash
# Verificar que estás en la raíz del proyecto
pwd  # Debe mostrar .../Audio2Text

# Verificar estructura
dir backend  # Debe existir
dir ui       # Debe existir
```

### Problema 6: Ejecutable no abre (SmartScreen)

**Solución:**
- Sigue la guía: `docs/INSTALACION.md`
- O ejecuta desde código fuente: `python main.py`

---

## 📊 Checklist Final

Antes de distribuir, verifica:

- [ ] ✅ Clonación exitosa
- [ ] ✅ Entorno virtual creado y activado
- [ ] ✅ Dependencias instaladas sin errores
- [ ] ✅ Aplicación ejecuta desde código fuente
- [ ] ✅ Compilación GENERAL exitosa
- [ ] ✅ Compilación de todas las variantes exitosa
- [ ] ✅ Ejecutables funcionan correctamente
- [ ] ✅ Build artifacts organizados
- [ ] ✅ Logs se generan correctamente
- [ ] ✅ Config.json se crea automáticamente

---

## 🎯 Resultado Esperado

Si todos los pasos anteriores funcionan:

✅ **El proyecto está 100% listo para distribución**

Cualquier persona con:
- Python 3.8+
- Git
- Groq API key

Puede:
1. Clonar el repositorio
2. Instalar dependencias
3. Ejecutar desde código fuente
4. Compilar ejecutables
5. Distribuir a clientes

---

## 📞 Soporte

Si encuentras algún problema no listado aquí:

1. Revisa los logs en `logs/`
2. Busca en [Issues](https://github.com/CENFARG/Audio2Text/issues)
3. Crea un nuevo issue con:
   - Descripción del problema
   - Pasos para reproducir
   - Logs relevantes
   - Sistema operativo y versión de Python

---

**Última actualización:** 2025-12-23  
**Versión:** 0.9.2  
**Estado:** ✅ Verificado y funcional
