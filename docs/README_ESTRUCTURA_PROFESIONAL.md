# 🏗️ Audio2Text v0.9.2 - Estructura Profesional

## 📋 Resumen Ejecutivo

Esta versión implementa una **estructura de proyecto profesional** con:
- ✅ Organización clara por tipos de archivo
- ✅ Separación de artefactos de compilación por variante
- ✅ Documentación centralizada
- ✅ Assets organizados
- ✅ Scripts de automatización

---

## 📁 Estructura del Proyecto

```
audio2text_v0.9.2/
│
├── 📂 assets/                    ← RECURSOS VISUALES
│   ├── icons/                    
│   │   └── icono.ico             (Ícono de la aplicación)
│   └── logos/                    
│       ├── logo.png              (Logo CENF/General)
│       ├── logo_contreras.png    (Logo Contreras Hnos)
│       └── logo_cutignola.png    (Logo Cutignola)
│
├── 📂 config/                    ← CONFIGURACIONES
│   ├── config.json               (Configuración de la app)
│   ├── version.json              (Info de versión para updates)
│   ├── version_info.txt          (Metadatos genéricos)
│   ├── version_info_GENERAL.txt  (Metadatos variante GENERAL)
│   ├── version_info_CONTRERAS.txt(Metadatos variante CONTRERAS)
│   └── version_info_CUTIGNOLA.txt(Metadatos variante CUTIGNOLA)
│
├── 📂 templates/                 ← TEMPLATES HTML
│   └── info_template.html        (Template para pestaña Info)
│
├── 📂 scripts/                   ← SCRIPTS DE BUILD
│   ├── build_GENERAL_v2.py       (Build variante GENERAL)
│   ├── build_CONTRERAS_v2.py     (Build variante CONTRERAS)
│   ├── build_CUTIGNOLA_v2.py     (Build variante CUTIGNOLA)
│   ├── build_all_v2.py           (Build maestro - todas las variantes)
│   ├── cleanup_build_artifacts.py(Limpieza de archivos antiguos)
│   └── update_build_paths.py     (Actualiza rutas en scripts)
│
├── 📂 docs/                      ← DOCUMENTACIÓN
│   ├── INSTALACION.md            (Guía para usuarios finales)
│   ├── GUIA_SMARTSCREEN.md       (Soluciones SmartScreen)
│   ├── RESUMEN_SOLUCIONES.md     (Resumen ejecutivo)
│   ├── README_v0.9.2.md          (README de la versión)
│   ├── GENERACION_COMPLETA.md    (Proceso de generación)
│   └── installer.nsi             (Script instalador NSIS)
│
├── 📂 backend/                   ← CÓDIGO BACKEND
│   ├── transcriber.py
│   ├── config_manager.py
│   ├── file_manager.py
│   └── ...
│
├── 📂 ui/                        ← CÓDIGO UI
│   ├── app.py
│   ├── tabs/
│   └── ...
│
├── 📂 lang/                      ← TRADUCCIONES
│   ├── en.json                   (Inglés)
│   └── es.json                   (Español)
│
├── 📂 _build_artifacts/          ← ARTEFACTOS DE COMPILACIÓN
│   ├── build/                    (Archivos temporales PyInstaller)
│   │   ├── GENERAL/
│   │   ├── CONTRERAS/
│   │   └── CUTIGNOLA/
│   ├── logs/                     (Logs de compilación)
│   │   ├── GENERAL/
│   │   │   ├── build_YYYYMMDD_HHMMSS.log
│   │   │   └── summary_YYYYMMDD_HHMMSS.txt
│   │   ├── CONTRERAS/
│   │   └── CUTIGNOLA/
│   ├── specs/                    (Archivos .spec de PyInstaller)
│   │   ├── GENERAL/
│   │   ├── CONTRERAS/
│   │   └── CUTIGNOLA/
│   └── legacy/                   (Archivos antiguos organizados)
│
├── 📂 dist/                      ← EJECUTABLES FINALES
│   ├── Audio2Text_CENF_0.9.2_GENERAL.exe
│   ├── Audio2Text_CENF_0.9.2_CONTRERAS.exe
│   └── Audio2Text_CENF_0.9.2_CUTIGNOLA.exe
│
├── 📄 main.py                    ← SCRIPT PRINCIPAL
├── 📄 requirements.txt           ← DEPENDENCIAS
├── 📄 organize_project.py        ← Script organizador (ejecutar una vez)
└── 📄 update_build_paths.py      ← Actualiza rutas (ejecutar una vez)
```

---

## 🚀 Guía de Uso

### 1️⃣ Primera Vez - Organizar Proyecto

Si vienes de una versión anterior sin estructura organizada:

```bash
# 1. Organizar archivos en carpetas profesionales
python organize_project.py

# 2. Actualizar rutas en scripts de build
python update_build_paths.py
```

### 2️⃣ Compilar Variantes

#### Opción A: Compilar todas las variantes
```bash
python scripts/build_all_v2.py
```

Esto compilará automáticamente:
- `Audio2Text_CENF_0.9.2_GENERAL.exe`
- `Audio2Text_CENF_0.9.2_CONTRERAS.exe`
- `Audio2Text_CENF_0.9.2_CUTIGNOLA.exe`

#### Opción B: Compilar una variante específica
```bash
# Solo GENERAL
python scripts/build_GENERAL_v2.py

# Solo CONTRERAS
python scripts/build_CONTRERAS_v2.py

# Solo CUTIGNOLA
python scripts/build_CUTIGNOLA_v2.py
```

### 3️⃣ Revisar Resultados

Después de compilar:

```bash
# Ejecutables en:
dist/

# Logs de compilación en:
_build_artifacts/logs/[VARIANTE]/

# Specs de PyInstaller en:
_build_artifacts/specs/[VARIANTE]/

# Build temp files en:
_build_artifacts/build/[VARIANTE]/
```

### 4️⃣ Limpiar Archivos Antiguos

Si tienes archivos .log y .spec antiguos en la raíz:

```bash
python scripts/cleanup_build_artifacts.py
```

Esto moverá todos los archivos antiguos a `_build_artifacts/legacy/`

---

## 🎯 Ventajas de Esta Estructura

### ✅ Claridad
- Todo tiene su lugar lógico
- Fácil encontrar cualquier archivo
- Nuevos desarrolladores entienden rápido

### ✅ Profesionalismo
- Estructura estándar de la industria
- Separación de concerns
- Escalable para futuro

### ✅ Mantenibilidad
- Logs organizados por variante y fecha
- Specs separados por cliente
- Build artifacts no ensucian el proyecto

### ✅ Versionado (Git)
```gitignore
# .gitignore sugerido
_build_artifacts/build/
_build_artifacts/logs/
dist/
__pycache__/
*.pyc
```

---

## 📝 Workflows Comunes

### Agregar un Nuevo Cliente (Variante)

1. **Crear logo del cliente:**
   ```
   assets/logos/logo_nombrecliente.png
   ```

2. **Crear version_info específico:**
   ```
   config/version_info_NOMBRECLIENTE.txt
   ```

3. **Crear script de build:**
   ```bash
   cp scripts/build_GENERAL_v2.py scripts/build_NOMBRECLIENTE_v2.py
   # Editar VARIANT = "NOMBRECLIENTE"
   # Editar LOGO_PATH = "assets/logos/logo_nombrecliente.png"
   ```

4. **Actualizar build_all_v2.py:**
   Agregar "NOMBRECLIENTE" a la lista de variantes

### Actualizar Logos de Cliente

```bash
# Simplemente reemplaza el archivo:
cp nuevo_logo.png assets/logos/logo_contreras.png

# Recompila esa variante:
python scripts/build_CONTRERAS_v2.py
```

### Generar Instalador NSIS

```bash
# 1. Compilar ejecutable primero
python scripts/build_GENERAL_v2.py

# 2. Generar instalador
"C:\Program Files (x86)\NSIS\makensis.exe" docs/installer.nsi
```

---

## 🔍 Troubleshooting

### Problema: "No se encuentra icono.ico"
**Solución:** Verifica que esté en `assets/icons/icono.ico`

### Problema: "No se encuentra config.json"
**Solución:** Verifica que esté en `config/config.json`

### Problema: Build falla con rutas incorrectas
**Solución:** 
```bash
python update_build_paths.py
```

### Problema: Logs antiguos en la raíz
**Solución:**
```bash
python scripts/cleanup_build_artifacts.py
```

---

## 📊 Comparación: Antes vs Ahora

### Antes (v0.9.0)
```
audio2text_v0.9.0/
├── logo.png ❌ (raíz desordenada)
├── icono.ico ❌
├── config.json ❌
├── version_info.txt ❌
├── build_0.8.1_20251022_113120.log ❌
├── Audio2Text_CENF_0.9.0.spec ❌
├── INSTALACION.md ❌
├── build/ ❌ (sin separar por variante)
└── ...
```

### Ahora (v0.9.2)
```
audio2text_v0.9.2/
├── assets/ ✅ (organizado)
│   ├── icons/
│   └── logos/
├── config/ ✅
├── templates/ ✅
├── scripts/ ✅
├── docs/ ✅
├── _build_artifacts/ ✅ (separado por variante)
│   ├── build/GENERAL/
│   ├── logs/GENERAL/
│   └── specs/GENERAL/
└── dist/ ✅
```

---

## 🎓 Mejores Prácticas

1. **Nunca editar archivos en `_build_artifacts/`** - Son temporales
2. **Documentar cambios** en `docs/`
3. **Logos en PNG** de buena resolución (300x300px mínimo)
4. **Logs se generan automáticamente** - No crearlos manualmente
5. **Usar scripts v2** para builds (tienen estructura organizada)

---

## 📚 Referencias

- **Guía de Instalación:** `docs/INSTALACION.md`
- **SmartScreen:** `docs/GUIA_SMARTSCREEN.md`
- **Changelog Completo:** `docs/README_v0.9.2.md`

---

**© 2024 CENF - Centro de Excelencia en Negocios del Futuro**

*Última actualización: 2025-12-22*
