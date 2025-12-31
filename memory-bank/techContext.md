# Technical Context

This file documents the technical stack, dependencies, and architecture decisions.
2025-05-06 20:21:11 - Log of updates made.

*

## Technology Stack

- **Frontend**: CustomTkinter (Python GUI framework)
- **Audio Processing**: PyAudio
- **AI/ML**: Groq API (Whisper Large v3)
- **System Integration**: PyAutoGUI, Keyboard, PsUtil
- **Data Storage**: JSON, File System
- **Development**: Python 3.8+

## Dependencies

- customtkinter: Interfaz gráfica moderna
- pyaudio: Captura y procesamiento de audio
- groq: Cliente API para transcripción
- python-dotenv: Gestión de variables de entorno
- pyautogui: Automatización de teclado y mouse
- keyboard: Detección de teclas presionadas
- psutil: Monitorización del sistema
- wave: Procesamiento de archivos WAV

## System Architecture

Aplicación de escritorio monolítica con arquitectura en capas:
- **Capa de Presentación**: Interfaz CustomTkinter con pestañas
- **Capa de Lógica**: Procesamiento de audio y configuración
- **Capa de Datos**: Sistema de archivos y JSON
- **Capa de Servicios**: Integración con APIs externas (Groq)