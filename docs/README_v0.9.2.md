# Audio2Text v0.9.2

## 🎯 Versión con Mejoras Anti-SmartScreen

Esta versión incluye todas las optimizaciones para reducir advertencias de Windows SmartScreen:

- ✅ Metadatos de versión profesionales
- ✅ Build optimizado (--noupx)
- ✅ Documentación completa de instalación
- ✅ Variantes personalizadas por cliente

## 📦 Variantes Disponibles

### 1. GENERAL (CENF)
Versión estándar de CENF con branding corporativo.

### 2. CONTRERAS
Versión personalizada para Contreras Hnos.

### 3. CUTIGNOLA
Versión personalizada para Cutignola.

## 🚀 Compilación

### Compilar una variante específica:
```bash
# Variante General
python build_GENERAL.py

# Variante Contreras
python build_CONTRERAS.py

# Variante Cutignola
python build_CUTIGNOLA.py
```

### Compilar todas las variantes:
```bash
python build_all.py
```

## 📝 Archivos de Configuración

Cada variante tiene:
- `version_info_[VARIANTE].txt` - Metadatos específicos
- `build_[VARIANTE].py` - Script de compilación

## 📄 Documentación

- `INSTALACION.md` - Guía para usuarios finales
- `GUIA_SMARTSCREEN.md` - Guía técnica sobre SmartScreen
- `RESUMEN_SOLUCIONES.md` - Resumen ejecutivo de soluciones

## 🔧 Requisitos

- Python 3.8+
- PyInstaller
- Dependencias en `requirements.txt`

## 📊 Changelog v0.9.2

- Metadatos de versión agregados para reducir advertencias SmartScreen
- Build optimizado con --noupx
- Documentación completa de instalación
- Script de instalador NSIS incluido
- Soporte para variantes personalizadas por cliente
- Scripts de build automatizados para cada variante

---

**© 2024 CENF - Centro de Excelencia en Negocios del Futuro**
