# Audio2Text

<div align="center">

![Audio2Text Logo](assets/logos/logo.png)

**Real-Time Audio Transcription with AI**

[![Version](https://img.shields.io/badge/version-0.9.3-blue.svg)](https://github.com/CENFARG/Audio2Text/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

[Features](#-features) •
[Installation](#-installation) •
[Usage](#-usage) •
[Documentation](#-documentation) •
[Contribute](#-contribute)

</div>

---

## 📖 Description

Audio2Text is a professional real-time audio transcription application that leverages the Whisper Large v3 model via the Groq API. Designed for businesses and professionals who need to convert audio to text quickly, accurately, and securely.

### 🎯 Use Cases

- 📝 Meeting and conference transcription
- 🎤 Voice notes to text
- 📞 Call logging
- 🎓 Class and seminar notes
- 💼 Interview documentation

## ✨ Features

### Key Functionalities

- 🎤 **Real-Time Transcription:** Powerd by Whisper Large v3 via Groq API
- 🌍 **Multi-language:** Full support for English and Spanish
- ⚡ **Global Hotkeys:** Configurable (F1-F12) for quick control
- 📁 **Automatic Management:** Smart file and log organization
- 🎨 **Professional Interface:** Modern UI built with CustomTkinter
- 🔄 **Auto-update:** Automatic update system
- 💾 **History:** Access to previous transcriptions
- 🎯 **System Tray:** Minimize to system tray

### Technical Features

- 🏗️ **Enterprise Architecture:** Modular and scalable code
- 🛡️ **Security:** No telemetry, data processed locally (audio sent to API securely)
- 📦 **Custom Build Support:** Client-specific builds
- 🔐 **Secure Configuration:** Secure handling of API keys
- 📊 **Detailed Logs:** Complete operation traceability

## 🚀 Installation

### For End Users

#### Option 1: Executable (Recommended)

1. Download the executable from [Releases](https://github.com/CENFARG/Audio2Text/releases/latest)
2. Run `Audio2Text_CENF_0.9.3_GENERAL.exe`
3. If SmartScreen appears, follow [this guide](docs/INSTALACION.md) (in Spanish)

#### Option 2: NSIS Installer

1. Download `Audio2Text_CENF_0.9.3_Setup.exe`
2. Run the installer
3. Follow on-screen instructions

### For Developers

```bash
# Clone repository
git clone https://github.com/CENFARG/Audio2Text.git
cd Audio2Text

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

## 🎮 Usage

### Initial Setup

1. **Get Groq API Key:**
   - Sign up at [Groq](https://groq.com)
   - Get your free API key
   - Copy the key

2. **Configure Audio2Text:**
   - Open the application
   - Go to the "Settings" tab
   - Paste your API key
   - Save changes

### Basic Usage

1. **Record Audio:**
   - Press the configured hotkey (default F2)
   - Speak clearly
   - Press again to stop

2. **View Transcription:**
   - Transcription appears automatically
   - Saved in history
   - Audio file saved in configured folder

### Advanced Usage

- **Change Language:** Settings → Language → Spanish/English
- **Customize Hotkey:** Settings → Hotkey → Select key
- **Manage Files:** "History" tab
- **View Logs:** `logs/` folder in installation directory

## 📦 Build from Source

### Build All Variants

```bash
python scripts/build_all_v2.py
```

### Build Specific Variant

```bash
# CENF (General)
python scripts/build_GENERAL_v2.py

# Contreras Hnos
python scripts/build_CONTRERAS_v2.py

# Cutignola
python scripts/build_CUTIGNOLA_v2.py
```

Executables are generated in `dist/`.

## 📚 Documentation

### User Documentation
*See Spanish documentation folder `docs/` for details.*

- **[Installation Guide](docs/INSTALACION.md)**
- **[SmartScreen Guide](docs/GUIA_SMARTSCREEN.md)**
- **[FAQ](docs/FAQ.md)**

### Technical Documentation

- **[Project Architecture](docs/README_ESTRUCTURA_PROFESIONAL.md)**
- **[Contribution Guide](CONTRIBUTING.md)**
- **[Security](SECURITY.md)**

## 🏗️ Project Structure

```
Audio2Text/
├── assets/              # Visual resources
│   ├── icons/          # App icons
│   └── logos/          # Logos per variant
├── backend/             # Business logic
│   ├── transcriber.py  # Transcription engine
│   ├── file_manager.py # File management
│   └── config_manager.py # Configuration
├── ui/                  # User Interface
│   ├── app.py          # Main application
│   ├── recording_overlay.py # Recording overlay
│   └── update_tab.py   # Updates tab
├── config/              # Configuration files
├── docs/                # Documentation
├── lang/                # Language files
├── scripts/             # Build scripts
├── templates/           # HTML Templates
├── main.py              # Entry point
└── requirements.txt     # Dependencies
```

## 🛠️ Technologies

- **Python 3.8+** - Main language
- **CustomTkinter** - Modern GUI
- **Groq API** - Transcription with Whisper Large v3
- **SoundDevice** - Audio capture
- **PyInstaller** - Executable packaging
- **Pillow** - Image processing
- **Keyboard** - Global hotkeys
- **Pystray** - System tray integration

## 🤝 Contribute

Contributions are welcome! Please read our [Contribution Guide](CONTRIBUTING.md) (Spanish) for details on:

- Code of Conduct
- Development Process
- How to report bugs
- How to suggest features
- Code Standards

## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

### Why Apache 2.0?

- ✅ **Patent Protection:** Grants explicit patent license
- ✅ **Trademark Protection:** Does not grant rights to "Audio2Text" or "CENF"
- ✅ **Commercial Use:** Allows use in enterprise environments
- ✅ **Modifications:** Allows modifications with attribution
- ✅ **Professional:** Enterprise standard (Google, Apache, Android)

## 🔒 Security

To report security vulnerabilities, please read our [Security Policy](SECURITY.md).

**DO NOT** report vulnerabilities in public issues.

## 👥 Authors

**CENF**

- Website: [cenfarg.com.ar](https://cenfarg.com.ar)
- Email: soporte@cenfarg.com.ar
- GitHub: [@CENFARG](https://github.com/CENFARG)

## 🙏 Acknowledgements

- [Groq](https://groq.com) for their amazing API
- [OpenAI](https://openai.com) for the Whisper model
- Python and Open Source Community

## 📞 Support

Need help?

- 📖 [Documentation](docs/)
- 📧 Email: soporte@cenfarg.com.ar

---

<div align="center">

**Made with ❤️ by CENF**

⭐ If you like this project, give it a star on GitHub!

</div>
