# 🎉 Crear Release v0.9.2 en GitHub

## 📋 Pasos para Crear la Release

### 1. Ir a GitHub Releases

1. Abre tu navegador
2. Ve a: https://github.com/CENFARG/Audio2Text/releases
3. Haz clic en **"Draft a new release"**

### 2. Configurar la Release

#### Tag Version
- **Tag:** `v0.9.2`
- **Target:** `main` branch
- Haz clic en "Create new tag: v0.9.2 on publish"

#### Release Title
```
v0.9.2 - Enterprise-Grade Release
```

#### Release Description

Copia y pega esto:

```markdown
# 🎉 Audio2Text v0.9.2 - Enterprise-Grade Release

## ⚠️ BREAKING CHANGES

**Estructura del Proyecto Reorganizada:**
- El código ahora está directamente en la raíz del repositorio (no en carpeta `audio2text_v0.9.2/`)
- Si ya tenías una copia local, recomendamos clonar de nuevo:
  ```bash
  git clone https://github.com/CENFARG/Audio2Text.git
  ```

---

## ✨ Novedades Principales

### 🏗️ Estructura Enterprise
- **Organización Profesional:** Código modular en carpetas especializadas (`assets/`, `backend/`, `config/`, `docs/`, etc.)
- **Estándares Python:** `setup.py`, `pyproject.toml` (PEP 518/621)
- **Licencia MIT:** Proyecto open-source profesional
- **Documentación Completa:** CHANGELOG, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY

### 🛡️ Soluciones Anti-SmartScreen
- **Metadatos Profesionales:** Ejecutables con información de empresa completa
- **Build Optimizado:** Flag `--noupx` para reducir falsos positivos
- **Documentación de Usuario:** Guía paso a paso para bypass de SmartScreen
- **Reducción Esperada:** 30-40% menos advertencias de Windows Defender

### 📦 Variantes Personalizadas
Tres builds específicos para diferentes clientes:
- **GENERAL** - CENF (Centro de Excelencia en Negocios del Futuro)
- **CONTRERAS** - Contreras Hnos
- **CUTIGNOLA** - Cliente Cutignola

Cada variante incluye:
- Logo personalizado
- Metadatos de empresa específicos
- Configuración adaptada

### 🔧 Sistema de Build Automatizado
- Scripts de compilación por variante
- Build artifacts organizados por cliente
- Logs con timestamp para trazabilidad
- Compilación de todas las variantes con un solo comando

### 📚 Documentación Profesional
- **README.md:** Completo con badges, estructura, y guías
- **CHANGELOG.md:** Historial de cambios (Keep a Changelog)
- **CONTRIBUTING.md:** Guía para contribuidores
- **SECURITY.md:** Política de seguridad y reporte de vulnerabilidades
- **Docs Técnicos:** Arquitectura, instalación, troubleshooting

### 🐛 GitHub Integration
- **Issue Templates:** Formularios estructurados para bugs y features
- **PR Template:** Checklist completo para pull requests
- **Workflows:** Preparado para CI/CD (próxima versión)

---

## 📥 Descargas

### Para Usuarios Finales

Descarga el ejecutable correspondiente a tu caso:

| Variante | Descripción | Descarga |
|----------|-------------|----------|
| **GENERAL** | CENF - Uso general | `Audio2Text_CENF_0.9.2_GENERAL.exe` |
| **CONTRERAS** | Contreras Hnos | `Audio2Text_CENF_0.9.2_CONTRERAS.exe` |
| **CUTIGNOLA** | Cliente Cutignola | `Audio2Text_CENF_0.9.2_CUTIGNOLA.exe` |

### Instalador (Recomendado)

- **Instalador NSIS:** `Audio2Text_CENF_0.9.2_Setup.exe`
  - Instalación profesional con accesos directos
  - Integración con Windows
  - Desinstalador incluido

### Para Desarrolladores

- **Código Fuente:** `Source code (zip)` o `Source code (tar.gz)`
- **Clonar:** `git clone https://github.com/CENFARG/Audio2Text.git`

---

## 📋 Requisitos

- **Sistema Operativo:** Windows 10/11 (64-bit)
- **Groq API Key:** Gratuita en [groq.com](https://groq.com)
- **Espacio en Disco:** ~100 MB

---

## 🚀 Inicio Rápido

### Opción 1: Ejecutable (Más Rápido)

1. Descarga el `.exe` correspondiente
2. Ejecuta el archivo
3. Si aparece SmartScreen, sigue [esta guía](https://github.com/CENFARG/Audio2Text/blob/main/docs/INSTALACION.md)
4. Configura tu API key de Groq
5. ¡Listo para usar!

### Opción 2: Desde Código

```bash
# Clonar
git clone https://github.com/CENFARG/Audio2Text.git
cd Audio2Text

# Instalar
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Ejecutar
python main.py
```

---

## 📖 Documentación

- **[README Principal](https://github.com/CENFARG/Audio2Text/blob/main/README.md)** - Información completa del proyecto
- **[Guía de Instalación](https://github.com/CENFARG/Audio2Text/blob/main/docs/INSTALACION.md)** - Instrucciones detalladas
- **[Solución SmartScreen](https://github.com/CENFARG/Audio2Text/blob/main/docs/GUIA_SMARTSCREEN.md)** - Cómo evitar advertencias
- **[Arquitectura](https://github.com/CENFARG/Audio2Text/blob/main/docs/README_ESTRUCTURA_PROFESIONAL.md)** - Estructura del proyecto
- **[Changelog Completo](https://github.com/CENFARG/Audio2Text/blob/main/CHANGELOG.md)** - Historial detallado

---

## 🔒 Seguridad

### Verificación de Ejecutables

Antes de ejecutar, verifica el hash SHA256:

```powershell
Get-FileHash Audio2Text_CENF_0.9.2_GENERAL.exe -Algorithm SHA256
```

**Hashes Oficiales:**
```
GENERAL:   [HASH_AQUI]
CONTRERAS: [HASH_AQUI]
CUTIGNOLA: [HASH_AQUI]
```

### Política de Seguridad

- ✅ Sin telemetría ni analytics
- ✅ Datos procesados localmente
- ✅ API calls solo a Groq (transcripción)
- ✅ Código open-source auditable

Ver [SECURITY.md](https://github.com/CENFARG/Audio2Text/blob/main/SECURITY.md) para reportar vulnerabilidades.

---

## 🐛 Problemas Conocidos

Ninguno en esta versión. Si encuentras alguno, por favor [reporta un issue](https://github.com/CENFARG/Audio2Text/issues/new?template=bug_report.yml).

---

## 🗺️ Próximos Pasos (v0.10.0)

- [ ] Soporte para más idiomas (Francés, Alemán, Portugués)
- [ ] Exportar a múltiples formatos (PDF, DOCX, TXT)
- [ ] Tests automatizados (pytest)
- [ ] CI/CD con GitHub Actions
- [ ] Integración con servicios en la nube

---

## 🙏 Agradecimientos

- **Groq** por su increíble API de transcripción
- **OpenAI** por el modelo Whisper
- **Comunidad Python** por las librerías utilizadas
- **Todos los contribuidores** que hicieron posible esta release

---

## 📞 Soporte

¿Necesitas ayuda?

- 📖 [Documentación](https://github.com/CENFARG/Audio2Text/tree/main/docs)
- 🐛 [Reportar Bug](https://github.com/CENFARG/Audio2Text/issues/new?template=bug_report.yml)
- 💡 [Sugerir Feature](https://github.com/CENFARG/Audio2Text/issues/new?template=feature_request.yml)
- 📧 Email: soporte@cenf.com.ar

---

<div align="center">

**Hecho con ❤️ por CENF**

⭐ Si te gusta este proyecto, ¡dale una estrella!

</div>
```

### 3. Adjuntar Archivos (Assets)

Si tienes los ejecutables compilados, súbelos aquí:

1. Haz clic en "Attach binaries"
2. Arrastra y suelta:
   - `Audio2Text_CENF_0.9.2_GENERAL.exe`
   - `Audio2Text_CENF_0.9.2_CONTRERAS.exe`
   - `Audio2Text_CENF_0.9.2_CUTIGNOLA.exe`
   - `Audio2Text_CENF_0.9.2_Setup.exe` (instalador NSIS)

**NOTA:** Si aún no has compilado, puedes:
- Publicar la release sin binarios (solo código fuente)
- Compilar después y editar la release para agregar los `.exe`

### 4. Opciones Adicionales

- ✅ **Set as the latest release** (marcar)
- ✅ **Create a discussion for this release** (opcional pero recomendado)
- ⬜ **Set as a pre-release** (NO marcar, es release estable)

### 5. Publicar

Haz clic en **"Publish release"**

---

## 📊 Después de Publicar

### Verificar la Release

1. Ve a https://github.com/CENFARG/Audio2Text/releases
2. Verifica que aparezca v0.9.2
3. Comprueba que los archivos se descarguen correctamente

### Generar Hashes SHA256

Si subiste los ejecutables, genera los hashes:

```powershell
cd dist  # O donde estén los .exe

Get-FileHash Audio2Text_CENF_0.9.2_GENERAL.exe -Algorithm SHA256 | Format-List
Get-FileHash Audio2Text_CENF_0.9.2_CONTRERAS.exe -Algorithm SHA256 | Format-List
Get-FileHash Audio2Text_CENF_0.9.2_CUTIGNOLA.exe -Algorithm SHA256 | Format-List
```

Luego **edita la release** y agrega los hashes en la sección correspondiente.

### Actualizar README Badges

El badge de versión se actualizará automáticamente:
```markdown
[![Version](https://img.shields.io/badge/version-0.9.2-blue.svg)](https://github.com/CENFARG/Audio2Text/releases)
```

---

## ✅ Checklist Final

Antes de publicar, verifica:

- [ ] Tag es `v0.9.2`
- [ ] Target es `main`
- [ ] Título es descriptivo
- [ ] Descripción está completa
- [ ] Archivos adjuntos (si aplica)
- [ ] "Set as latest release" marcado
- [ ] Hashes SHA256 agregados (después de subir archivos)

---

**¡Listo! Tu release profesional está publicada.** 🎉
