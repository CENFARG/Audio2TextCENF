**[Español](VERIFICACION_INSTALACION.md) | [English](VERIFICACION_INSTALACION_EN.md)**

# 🧪 Verification Guide - Audio2Text v0.9.4

This guide verifies that anyone can clone, install, run, and compile the project without issues.

---

## ✅ Complete Verification Checklist

### 1. Clone the Repository

```bash
# Clone
git clone https://github.com/CENFARG/Audio2Text.git
cd Audio2Text

# Verify structure
dir  # Windows
# or
ls   # Linux/Mac
```

**Must show:**
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

✅ **Verified:** Full structure present

---

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Verify creation
dir .venv  # Must exist
```

✅ **Verified:** Virtual environment created

---

### 3. Activate Virtual Environment

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

**Verify activation:**
```bash
python --version  # Must show Python 3.8+
which python      # Must point to .venv
```

✅ **Verified:** Environment activated correctly

---

### 4. Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Verify installation:**
```bash
pip list
```

**Must include:**
- customtkinter
- groq
- sounddevice
- Pillow
- pyinstaller
- (and all others from requirements.txt)

✅ **Verified:** All dependencies installed

---

### 5. Configure API Key (Temporary for Testing)

Create a temporary `config/config.json` file:

```json
{
    "groq_api_key": "YOUR_API_KEY_HERE",
    "default_language": "en",
    "hotkey": "F2",
    "audio_path": "audio",
    "logs_path": "logs",
    "max_audio_size_mb": 100,
    "max_log_size_mb": 50
}
```

**NOTE:** This file is NOT uploaded to Git (it is in .gitignore)

✅ **Verified:** Configuration created

---

### 6. Run from Source

```bash
python main.py
```

**Must:**
- ✅ Open the Audio2Text window
- ✅ Show 3 tabs (Main, Settings, Info)
- ✅ Allow configuring the API key
- ✅ Allow recording audio (with valid API key)

**Verify logs:**
```bash
dir logs  # Must have an app_YYYYMMDD_HHMMSS.log file
```

✅ **Verified:** Application runs correctly

---

### 7. Compile Executable (GENERAL Variant)

```bash
# Compile GENERAL variant
python scripts/build_GENERAL_v2.py
```

**Expected process:**
```
🔨 Compiling Audio2Text CENF 0.9.4 - Variant: GENERAL
📋 Verifying dependencies...
✅ PyInstaller found
🧹 Cleaning previous builds...
🏗️  Running PyInstaller...
...
✅ Build completed successfully!
📦 Executable: dist\Audio2Text_CENF_0.9.4_GENERAL.exe
```

**Verify:**
```bash
dir dist  # Audio2Text_CENF_0.9.4_GENERAL.exe must exist
```

✅ **Verified:** Compilation successful

---

### 8. Test Compiled Executable

```bash
# Run the .exe
.\dist\Audio2Text_CENF_0.9.4_GENERAL.exe
```

**Must:**
- ✅ Open without errors
- ✅ Function identical to source code
- ✅ Create config.json if not exists
- ✅ Create audio/ and logs/ folders

✅ **Verified:** Executable works correctly

---

### 9. Compile All Variants

```bash
# Compile all 3 variants
python scripts/build_all_v2.py
```

**Must generate:**
```
dist/
├── Audio2Text_CENF_0.9.4_GENERAL.exe
├── Audio2Text_CENF_0.9.4_CONTRERAS.exe
└── Audio2Text_CENF_0.9.4_CUTIGNOLA.exe
```

**Verify sizes:**
```bash
dir dist\*.exe
```

Each .exe should be ~80-120 MB approximately.

✅ **Verified:** All variants compiled

---

### 10. Verify Build Artifacts

```bash
dir _build_artifacts
```

**Must contain:**
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

✅ **Verified:** Artifacts organized correctly

---

## 🐛 Common Issues and Solutions

### Issue 1: "python not recognized"

**Solution:**
```bash
# Verify Python installation
python --version

# If fails, add Python to PATH
# Or use:
py --version  # Windows
python3 --version  # Linux/Mac
```

### Issue 2: "No module named 'customtkinter'"

**Solution:**
```bash
# Verify virtual environment is activated
# (.venv) should appear at prompt start

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue 3: "Permission denied" activating .venv

**Solution (Windows PowerShell):**
```powershell
# Run as administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
.venv\Scripts\Activate.ps1
```

### Issue 4: PyInstaller build error

**Solution:**
```bash
# Clean previous builds
python scripts/cleanup_build_artifacts.py

# Reinstall PyInstaller
pip uninstall pyinstaller
pip install pyinstaller>=6.0.0

# Try again
python scripts/build_GENERAL_v2.py
```

### Issue 5: "ModuleNotFoundError: No module named 'backend'"

**Solution:**
```bash
# Verify you are in project root
pwd  # Should show .../Audio2Text

# Verify structure
dir backend  # Must exist
dir ui       # Must exist
```

### Issue 6: Executable won't open (SmartScreen)

**Solution:**
- Follow guide: `docs/INSTALACION.md`
- Or run from source: `python main.py`

---

## 📊 Final Checklist

Before distributing, verify:

- [ ] ✅ Successful clone
- [ ] ✅ Virtual environment created and activated
- [ ] ✅ Dependencies installed without errors
- [ ] ✅ App runs from source
- [ ] ✅ Successful GENERAL compilation
- [ ] ✅ Successful compilation of all variants
- [ ] ✅ Executables work correctly
- [ ] ✅ Build artifacts organized
- [ ] ✅ Logs generated correctly
- [ ] ✅ Config.json created automatically

---

## 🎯 Expected Result

If all steps above work:

✅ **Project is 100% ready for distribution**

Anyone with:
- Python 3.8+
- Git
- Groq API key

Can:
1. Clone the repository
2. Install dependencies
3. Run from source
4. Compile executables
5. Distribute to clients

---

## 📞 Support

If you find an issue not listed here:

1. Check logs in `logs/`
2. Search [Issues](https://github.com/CENFARG/Audio2Text/issues)
3. Create a new issue with:
   - Problem description
   - Steps to reproduce
   - Relevant logs
   - OS and Python version

---

**Last updated:** 2025-12-31
**Version:** 0.9.4
**Status:** ✅ Verified and functional
