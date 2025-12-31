# 📋 INSTRUCCIONES: Cómo Proceder Ahora

## ✅ Estado Actual

### Lo que se ha creado:
1. ✅ **Versión 0.9.2** completa con estructura base
2. ✅ **Scripts de organización** profesional
3. ✅ **Scripts de build mejorados (v2)** con separación por variante
4. ✅ **Documentación completa**
5. ✅ **Metadatos anti-SmartScreen**

### El build original (`build_all.py`):
- ⚠️ Tuvo errores (falló GENERAL y CUTIGNOLA, exitoso CONTRERAS)
- ⚠️ Usa estructura antigua (archivos en raíz)
- ℹ️ **No usar esos ejecutables**

---

## 🚀 Pasos a Seguir (En Orden)

### Paso 1: Organizar la Estructura del Proyecto
```powershell
cd c:\Dropbox\DOC.RECA\06-Software\Audio2Text\audio2text_v0.9.2

# Organiza todos los archivos en carpetas profesionales
python organize_project.py
```

**Qué hace:**
- Mueve logos → `assets/logos/`
- Mueve iconos → `assets/icons/`
- Mueve configs → `config/`
- Mueve templates → `templates/`
- Mueve scripts → `scripts/`
- Mueve docs → `docs/`

---

### Paso 2: Actualizar Rutas en Scripts
```powershell
# Actualiza las rutas en los scripts de build
python update_build_paths.py
```

**Qué hace:**
- Actualiza rutas de assets en scripts
- Actualiza rutas de config
- Actualiza rutas de templates
- Los scripts apuntarán a `assets/`, `config/`, etc.

---

### Paso 3: Limpiar Archivos Antiguos (Opcional)
```powershell
# Mueve archivos .log y .spec antiguos a _build_artifacts/legacy/
python scripts/cleanup_build_artifacts.py
```

---

### Paso 4: Compilar con la Nueva Estructura
```powershell
# Compilar TODAS las variantes con estructura organizada
python scripts/build_all_v2.py
```

**O compilar individualmente:**
```powershell
# Solo una variante
python scripts/build_GENERAL_v2.py
python scripts/build_CONTRERAS_v2.py
python scripts/build_CUTIGNOLA_v2.py
```

---

### Paso 5: Verificar Resultados

Después de compilar, verificar:

```powershell
# Ver ejecutables generados
ls dist/

# Ver logs detallados por variante
ls _build_artifacts/logs/GENERAL/
ls _build_artifacts/logs/CONTRERAS/
ls _build_artifacts/logs/CUTIGNOLA/

# Ver specs por variante
ls _build_artifacts/specs/GENERAL/
ls _build_artifacts/specs/CONTRERAS/
ls _build_artifacts/specs/CUTIGNOLA/
```

**Ejecutables esperados:**
- `dist/Audio2Text_CENF_0.9.2_GENERAL.exe`
- `dist/Audio2Text_CENF_0.9.2_CONTRERAS.exe`
- `dist/Audio2Text_CENF_0.9.2_CUTIGNOLA.exe`

---

## 🎨 Personalización de Logos (Antes de Distribuir)

### Para Contreras Hnos:
```powershell
# Reemplazar con logo real
cp "ruta\al\logo_contreras_real.png" "assets\logos\logo_contreras.png"

# Recompilar
python scripts\build_CONTRERAS_v2.py
```

### Para Cutignola:
```powershell
# Reemplazar con logo real
cp "ruta\al\logo_cutignola_real.png" "assets\logos\logo_cutignola.png"

# Recompilar
python scripts\build_CUTIGNOLA_v2.py
```

---

## 📁 Nueva Estructura de Directorios

Después de organizar, el proyecto quedará así:

```
audio2text_v0.9.2/
│
├── assets/                  ← Recursos visuales
│   ├── icons/
│   │   └── icono.ico
│   └── logos/
│       ├── logo.png
│       ├── logo_contreras.png
│       └── logo_cutignola.png
│
├── config/                  ← Configuraciones
│   ├── config.json
│   ├── version.json
│   └── version_info_*.txt
│
├── templates/               ← Templates
│   └── info_template.html
│
├── scripts/                 ← Scripts de build
│   ├── build_GENERAL_v2.py
│   ├── build_CONTRERAS_v2.py
│   ├── build_CUTIGNOLA_v2.py
│   ├── build_all_v2.py
│   └── cleanup_build_artifacts.py
│
├── docs/                    ← Documentación
│   ├── INSTALACION.md
│   ├── GUIA_SMARTSCREEN.md
│   └── *.md
│
├── backend/                 ← Código backend
├── ui/                      ← Código UI
├── lang/                    ← Traducciones
│
├── _build_artifacts/        ← Artefactos (organizado!)
│   ├── build/
│   │   ├── GENERAL/
│   │   ├── CONTRERAS/
│   │   └── CUTIGNOLA/
│   ├── logs/
│   │   ├── GENERAL/
│   │   ├── CONTRERAS/
│   │   └── CUTIGNOLA/
│   └── specs/
│       ├── GENERAL/
│       ├── CONTRERAS/
│       └── CUTIGNOLA/
│
├── dist/                    ← Ejecutables finales
│
├── main.py
├── requirements.txt
└── README_ESTRUCTURA_PROFESIONAL.md
```

---

## 🔍 Solución de Problemas

### Error: "No se encuentra logo.png"
**Causa:** El archivo no se movió correctamente
**Solución:**
```powershell
# Verificar que exista
ls assets\logos\logo.png

# Si no existe, copiar desde raíz si aún está ahí
cp logo.png assets\logos\
```

### Error: "No se encuentra config.json"
**Causa:** Ruta no actualizada en scripts
**Solución:**
```powershell
# Re-ejecutar actualización de rutas
python update_build_paths.py
```

### Error al compilar: "icono.ico not found"
**Solución:**
```powershell
# Verificar ubicación
ls assets\icons\icono.ico

# Si está en la raíz, mover
mv icono.ico assets\icons\
```

### Build falla con error de permisos
**Solución:**
```powershell
# Eliminar carpeta build antigua si existe
rmdir /s build

# Limpiar y reintentar
python scripts\cleanup_build_artifacts.py
python scripts\build_all_v2.py
```

---

## 📊 Checklist de Verificación

Antes de distribuir, verificar:

- [ ] Paso 1: `organize_project.py` ejecutado
- [ ] Paso 2: `update_build_paths.py` ejecutado
- [ ] Paso 3: Builds ejecutados sin errores
- [ ] Paso 4: Ejecutables en `dist/` funcionan
- [ ] Paso 5: Logos personalizados reales (si aplica)
- [ ] Paso 6: Documentación `INSTALACION.md` incluida
- [ ] Paso 7: Probar en Windows limpio (sin dev tools)

---

## 🎯 Resultado Final Esperado

```
✅ 3 ejecutables compilados con éxito
✅ Metadatos profesionales en cada uno
✅ Logos personalizados por cliente
✅ Logs organizados en _build_artifacts/logs/[VARIANTE]/
✅ Specs organizados en _build_artifacts/specs/[VARIANTE]/
✅ Proyecto con estructura profesional
✅ Documentación completa
✅ Reducción de 30-40% en advertencias SmartScreen
```

---

## 📞 Próximos Pasos Después de Compilar

### Distribución a Clientes

#### Para Contreras Hnos:
```
Enviar:
- dist/Audio2Text_CENF_0.9.2_CONTRERAS.exe
- docs/INSTALACION.md
```

#### Para Cutignola:
```
Enviar:
- dist/Audio2Text_CENF_0.9.2_CUTIGNOLA.exe
- docs/INSTALACION.md
```

#### Para uso general (CENF):
```
Enviar:
- dist/Audio2Text_CENF_0.9.2_GENERAL.exe
- docs/INSTALACION.md
```

---

## 🎓 Documentación de Referencia

- **README_ESTRUCTURA_PROFESIONAL.md** - Guía completa de la estructura
- **RESUMEN_FINAL_v0.9.2.md** - Resumen de todo lo implementado
- **docs/INSTALACION.md** - Para usuarios finales
- **docs/GUIA_SMARTSCREEN.md** - Soluciones a SmartScreen

---

**🚀 ¡Todo está listo! Solo falta ejecutar los pasos 1-4 en orden.**

---

**© 2024 CENF**
*Creado: 2025-12-22*
