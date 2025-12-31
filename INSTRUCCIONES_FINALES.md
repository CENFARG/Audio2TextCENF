# 🎯 INSTRUCCIONES FINALES - Reorganización Audio2Text

## ✅ LO QUE YA ESTÁ LISTO

### 1. Archivos Organizados
- ✅ 23 items archivados en `_old_versions_archive/`
- ✅ Contenido de v0.9.2 movido a raíz
- ✅ Estructura profesional en la raíz:
  ```
  Audio2Text/
  ├── assets/         # Logos e iconos
  ├── backend/        # Lógica
  ├── config/         # Configuraciones
  ├── docs/           # Documentación
  ├── lang/           # Idiomas
  ├── scripts/        # Builds
  ├── templates/      # HTML
  ├── ui/             # Interfaz
  ├── main.py         # App principal
  └── requirements.txt
  ```

### 2. Git Configurado
- ✅ `.gitignore` actualizado
- ✅ `_old_versions_archive/` ignorado
- ✅ README.md actualizado

## ⚠️ PASOS FINALES MANUALES

### PASO 1: Cerrar Archivos Bloqueados

**Cierra TODOS los archivos abiertos en tu editor** (especialmente):
- `audio2text_v0.9.0/`
- `audio2text_v0.9.2/`
- `.env`

### PASO 2: Completar la Limpieza

Ejecuta estos comandos en PowerShell:

```powershell
cd "c:\Dropbox\DOC.RECA\06-Software\Audio2Text"

# Mover carpetas de versiones al archivo
Move-Item -Path "audio2text_v0.9.0\" -Destination "_old_versions_archive\" -Force
Move-Item -Path "audio2text_v0.9.2\" -Destination "_old_versions_archive\" -Force

# Mover scripts temporales
Move-Item -Path "final_cleanup_master.py" -Destination "_old_versions_archive\" -Force

# Mover carpetas restantes si existen
if (Test-Path "build\") { Move-Item -Path "build\" -Destination "_old_versions_archive\" -Force }
if (Test-Path "dist\") { Move-Item -Path "dist\" -Destination "_old_versions_archive\" -Force }
if (Test-Path "audio\") { Move-Item -Path "audio\" -Destination "_old_versions_archive\" -Force }
```

### PASO 3: Verificar Estructura

```powershell
# Ver qué quedó en la raíz
Get-ChildItem | Where-Object {$_.Name -notlike ".*" -and $_.Name -notlike "_*"} | Sort-Object Name
```

Deberías ver SOLO:
- 📁 `assets/`
- 📁 `backend/`
- 📁 `config/`
- 📁 `docs/`
- 📁 `lang/`
- 📁 `scripts/`
- 📁 `templates/`
- 📁 `ui/`
- 📄 `COMMIT_MESSAGE.md`
- 📄 `GEMINI.md`
- 📄 `main.py`
- 📄 `README.md`
- 📄 `requirements.txt`

### PASO 4: Preparar Git

```powershell
# Ver qué cambió
git status

# Debería mostrar:
# - Archivos modificados: .gitignore, README.md, GEMINI.md
# - Archivos nuevos: toda la estructura de v0.9.2
# - Archivos eliminados: audio2text_v0.9.0/, audio2text_v0.9.2/
```

### PASO 5: Agregar Cambios a Git

```powershell
# Agregar todo (incluyendo eliminaciones)
git add -A

# Verificar qué va en el commit
git status
```

## 🚨 IMPORTANTE - ANTES DE COMMITEAR

Este commit va a **cambiar completamente la estructura** de tu repositorio:

### ANTES (GitHub actual):
```
Audio2Text/
├── audio2text_v0.9.2/  # ← Todo dentro de una carpeta
│   ├── main.py
│   ├── backend/
│   └── ...
└── README.md
```

### DESPUÉS (lo que subirás):
```
Audio2Text/
├── main.py             # ← Directamente en la raíz
├── backend/
├── assets/
└── ...
```

### ⚠️ IMPACTO
- Los usuarios que ya clonaron el repo deberán:
  - Hacer `git pull` y resolver conflictos, O
  - Clonar de nuevo desde cero
  
- Esta es una **reorganización mayor** pero **profesional**

## PASO 6: Hacer el Commit

```powershell
git commit -m "Refactor: Estructura raíz profesional v0.9.2" -m "BREAKING CHANGE: Movido contenido de audio2text_v0.9.2/ a raíz del proyecto" -m "- Estructura enterprise directamente en raíz" -m "- Versiones antiguas archivadas localmente" -m "- README y documentación actualizados" -m "- Los usuarios deben re-clonar o hacer clean pull"
```

## PASO 7 Push a GitHub

```powershell
git push origin main
```

## PASO 8: Crear Release en GitHub (Opcional pero Recomendado)

1. Ve a GitHub → Releases → New Release
2. Tag: `v0.9.2`
3. Title: `v0.9.2 - Estructura Profesional + Soluciones SmartScreen`
4. Description:
   ```markdown
   ## ⚠️ BREAKING CHANGE
   
   La estructura del repositorio cambió. Si ya tenías una copia local, 
   recomendamos clonar de nuevo.
   
   ## ✨ Novedades
   - Estructura profesional en la raíz del proyecto
   - Metadatos anti-SmartScreen
   - 3 variantes de cliente (GENERAL, CONTRERAS, CUTIGNOLA)
   - Documentación completa
   
   ## 📦 Descargas
   - Audio2Text_CENF_0.9.2_GENERAL.exe
   - Audio2Text_CENF_0.9.2_CONTRERAS.exe
   - Audio2Text_CENF_0.9.2_CUTIGNOLA.exe
   ```
5. Adjunta los `.exe` compilados (desde `_build_artifacts/` si los tienes)

## ✅ CHECKLIST FINAL

Antes de hacer push, verifica:

- [ ] Cerraste todos los archivos abiertos
- [ ] Moviste `audio2text_v0.9.0/` y `audio2text_v0.9.2/` al archivo
- [ ] `git status` muestra solo la estructura correcta
- [ ] Probaste que `python main.py` funciona desde la raíz
- [ ] El commit message explica el BREAKING CHANGE
- [ ] Estás listo para que otros usuarios re-clonen

---

## 🆘 SI ALGO SALE MAL

### Deshacer todo (antes del push):
```powershell
git reset --hard HEAD
```

### Deshacer después del push:
```powershell
git revert HEAD
git push origin main
```

---

**Fecha:** 2025-12-22  
**Versión final:** 0.9.2  
**Autor:** Proyecto Audio2Text - CENF
