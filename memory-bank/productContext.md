# Product Context

This file provides a high-level overview of the project and the expected product that will be created. Initially it is based upon projectBrief.md (if provided) and all other available project-related information in the working directory. This file is intended to be updated as the project evolves, and should be used to inform all other modes of the project's goals and context.
2025-05-06 20:20:33 - Log of updates made will be appended as footnotes to the end of this file.

*

## Project Goal

Crear una aplicación avanzada de transcripción de audio a texto con funcionalidades de almacenamiento, configuración y gestión de archivos.

## Key Features

- Transcripción de audio en tiempo real usando Groq API
- Sistema de almacenamiento de archivos de audio en carpeta dedicada
- Gestión de logs de transcripciones en formato JSON
- Interfaz de configuración con pestañas para personalización
- Sistema de teclas de acceso rápido personalizables (F1-F12)
- Indicadores de tamaño de archivos y logs
- Funciones de borrado y limpieza de archivos
- Soporte para múltiples idiomas (español e inglés)
- Interfaz gráfica moderna con CustomTkinter

## Overall Architecture

Aplicación de escritorio basada en Python que utiliza:
- CustomTkinter para la interfaz gráfica
- PyAudio para la captura de audio
- Groq API para la transcripción
- Sistema de archivos para almacenamiento
- JSON para configuración y logs