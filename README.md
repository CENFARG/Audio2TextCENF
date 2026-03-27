# Audio2Text

<div align="center">

![Audio2Text Logo](assets/logos/logo.png)

**Transcripción de Audio en Tiempo Real con IA**

[![Version](https://img.shields.io/badge/version-0.9.2-blue.svg)](https://github.com/CENFARG/Audio2Text/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

[Características](#-características) •
[Instalación](#-instalación) •
[Uso](#-uso) •
[Documentación](#-documentación) •
[Contribuir](#-contribuir)

</div>

---

## 📖 Descripción

Audio2Text es una aplicación profesional de transcripción de audio en tiempo real que utiliza el modelo Whisper Large v3 a través de la API de Groq. Diseñada para empresas y profesionales que necesitan convertir audio a texto de manera rápida, precisa y segura.

### 🎯 Casos de Uso

- 📝 Transcripción de reuniones y conferencias
- 🎤 Notas de voz a texto
- 📞 Registro de llamadas telefónicas
- 🎓 Apuntes de clases y seminarios
- 💼 Documentación de entrevistas

## ✨ Características

### Funcionalidades Principales

- 🎤 **Transcripción en Tiempo Real:** Usando Whisper Large v3 via Groq API
- 🌍 **Multiidioma:** Soporte completo para Español e Inglés
- ⚡ **Hotkeys Globales:** Configurables (F1-F12) para control rápido
- 📁 **Gestión Automática:** Organización inteligente de archivos y logs
- 🎨 **Interfaz Profesional:** UI moderna con CustomTkinter
- 🔄 **Auto-actualización:** Sistema de updates automático
- 💾 **Historial:** Acceso a transcripciones anteriores
- 🎯 **System Tray:** Minimizar a bandeja del sistema

### Características Técnicas

- 🏗️ **Arquitectura Enterprise:** Código modular y escalable
- 🛡️ **Seguridad:** Sin telemetría, datos procesados localmente
- 📦 **Variantes Personalizadas:** Builds específicos por cliente
- 🔐 **Metadatos Profesionales:** Ejecutables con firma de empresa
- 📊 **Logs Detallados:** Trazabilidad completa de operaciones

## 🚀 Instalación

### Para Usuarios Finales

#### Opción 1: Ejecutable (Recomendado)

1. Descarga el ejecutable de [Releases](https://github.com/CENFARG/Audio2Text/releases/latest)
2. Ejecuta `Audio2Text_CENF_0.9.2_GENERAL.exe`
3. Si aparece SmartScreen, sigue [esta guía](docs/INSTALACION.md)

#### Opción 2: Instalador NSIS

1. Descarga `Audio2Text_CENF_0.9.2_Setup.exe`
2. Ejecuta el instalador
3. Sigue las instrucciones en pantalla

### Para Desarrolladores

```bash
# Clonar repositorio
git clone https://github.com/CENFARG/Audio2Text.git
cd Audio2Text

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python main.py
```

## 🎮 Uso

### Configuración Inicial

1. **Obtener API Key de Groq:**
   - Regístrate en [Groq](https://groq.com)
   - Obtén tu API key gratuita
   - Copia la key

2. **Configurar Audio2Text:**
   - Abre la aplicación
   - Ve a la pestaña "Configuración"
   - Pega tu API key
   - Guarda los cambios

### Uso Básico

1. **Grabar Audio:**
   - Presiona el hotkey configurado (por defecto F2)
   - Habla claramente
   - Presiona nuevamente para detener

2. **Ver Transcripción:**
   - La transcripción aparecerá automáticamente
   - Se guarda en el historial
   - Archivo de audio guardado en carpeta configurada

### Uso Avanzado

- **Cambiar Idioma:** Configuración → Idioma → Español/Inglés
- **Personalizar Hotkey:** Configuración → Hotkey → Seleccionar tecla
- **Gestionar Archivos:** Pestaña "Archivos Guardados"
- **Ver Logs:** Carpeta `logs/` en directorio de instalación

## 📦 Compilar desde Código

### Compilar Todas las Variantes

```bash
python scripts/build_all_v2.py
```

### Compilar Variante Específica

```bash
# CENF (General)
python scripts/build_GENERAL_v2.py

# Contreras Hnos
python scripts/build_CONTRERAS_v2.py

# Cutignola
python scripts/build_CUTIGNOLA_v2.py
```

Los ejecutables se generan en `dist/`

### Crear Instalador NSIS

```bash
# Requiere NSIS instalado
cd docs
makensis installer.nsi
```

## � Documentación

### Documentación de Usuario

- **[Guía de Instalación](docs/INSTALACION.md)** - Instrucciones detalladas
- **[Solución SmartScreen](docs/GUIA_SMARTSCREEN.md)** - Cómo evitar advertencias
- **[Preguntas Frecuentes](docs/FAQ.md)** - Respuestas a dudas comunes

### Documentación Técnica

- **[Arquitectura del Proyecto](docs/README_ESTRUCTURA_PROFESIONAL.md)** - Estructura y diseño
- **[Guía de Contribución](CONTRIBUTING.md)** - Cómo contribuir
- **[Changelog](CHANGELOG.md)** - Historial de cambios
- **[Seguridad](SECURITY.md)** - Política de seguridad

## 🏗️ Estructura del Proyecto

```
Audio2Text/
├── assets/              # Recursos visuales
│   ├── icons/          # Iconos de la aplicación
│   └── logos/          # Logos por variante
├── backend/             # Lógica de negocio
│   ├── transcriber.py  # Motor de transcripción
│   ├── file_manager.py # Gestión de archivos
│   └── config_manager.py # Configuración
├── ui/                  # Interfaz gráfica
│   ├── app.py          # Aplicación principal
│   ├── recording_overlay.py # Overlay de grabación
│   └── update_tab.py   # Pestaña de updates
├── config/              # Configuraciones
│   └── version_info_*.txt # Metadatos por variante
├── docs/                # Documentación
├── lang/                # Archivos de idioma
├── scripts/             # Scripts de build
├── templates/           # Templates HTML
├── main.py              # Punto de entrada
└── requirements.txt     # Dependencias
```

## �️ Tecnologías

- **Python 3.8+** - Lenguaje principal
- **CustomTkinter** - Interfaz gráfica moderna
- **Groq API** - Transcripción con Whisper Large v3
- **SoundDevice** - Captura de audio
- **PyInstaller** - Empaquetado de ejecutables
- **Pillow** - Procesamiento de imágenes
- **Keyboard** - Hotkeys globales
- **Pystray** - Integración system tray

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor lee nuestra [Guía de Contribución](CONTRIBUTING.md) para detalles sobre:

- Código de conducta
- Proceso de desarrollo
- Cómo reportar bugs
- Cómo sugerir mejoras
- Estándares de código

### Inicio Rápido para Contribuidores

1. Fork el proyecto
2. Crea tu rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'feat: Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia Apache 2.0 - ver el archivo [LICENSE](LICENSE) para detalles.

### ¿Por qué Apache 2.0?

- ✅ **Protección de Patentes:** Otorga licencia de patentes explícita
- ✅ **Protección de Marca:** No otorga derechos sobre "Audio2Text" o "CENF"
- ✅ **Uso Comercial:** Permite uso en entornos empresariales
- ✅ **Modificaciones:** Permite modificaciones con atribución
- ✅ **Profesional:** Estándar enterprise (Google, Apache, Android)

## 🔒 Seguridad

Para reportar vulnerabilidades de seguridad, por favor lee nuestra [Política de Seguridad](SECURITY.md).

**NO** reportes vulnerabilidades en issues públicos.

## 👥 Autores

**CENF**

- Website: [cenfarg.com.ar](https://cenfarg.com.ar)
- Email: cenf.arg@gmail.com
- GitHub: [@CENFARG](https://github.com/CENFARG)

## � Agradecimientos

- [Groq](https://groq.com) por su increíble API
- [OpenAI](https://openai.com) por el modelo Whisper
- Comunidad de Python y open source

## �📞 Soporte

¿Necesitas ayuda?

- 📖 [Documentación](docs/)
- 🐛 [Reportar Bug](https://github.com/CENFARG/Audio2Text/issues/new?template=bug_report.yml)
- 💡 [Sugerir Feature](https://github.com/CENFARG/Audio2Text/issues/new?template=feature_request.yml)
- 💬 [Discussions](https://github.com/CENFARG/Audio2Text/discussions)
- 📧 Email: cenf.arg@gmail.com

## 🗺️ Roadmap

### v0.10.0 (Próximo)
- [ ] Soporte para más idiomas
- [ ] Exportar a múltiples formatos (PDF, DOCX)
- [ ] Integración con servicios en la nube
- [ ] Tests automatizados

### v1.0.0 (Futuro)
- [ ] Versión para Linux y macOS
- [ ] API REST para integración
- [ ] Modo batch para múltiples archivos
- [ ] Interfaz web opcional

Ver [Issues](https://github.com/CENFARG/Audio2Text/issues) para más detalles.

## 📊 Estado del Proyecto

![GitHub last commit](https://img.shields.io/github/last-commit/CENFARG/Audio2Text)
![GitHub issues](https://img.shields.io/github/issues/CENFARG/Audio2Text)
![GitHub pull requests](https://img.shields.io/github/issues-pr/CENFARG/Audio2Text)

---

<div align="center">

**Hecho con ❤️ por CENF**

⭐ Si te gusta este proyecto, dale una estrella en GitHub!

</div>
