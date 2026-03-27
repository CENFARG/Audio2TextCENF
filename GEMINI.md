# Project Overview

This project, **Audio2Text**, is a real-time audio transcription application developed in Python. It leverages the Groq API with the Whisper Large v3 model to provide fast and accurate transcriptions. The application features a graphical user interface (GUI) built with the CustomTkinter library, allowing for an intuitive user experience.

## Main Technologies

*   **Backend:** Python
*   **GUI:** CustomTkinter
*   **Audio Processing:** PyAudio
*   **Transcription:** Groq API (Whisper Large v3)
*   **Hotkeys:** keyboard
*   **System Tray:** pystray

## Key Features

*   **Real-time Transcription:** Transcribes audio from the microphone in real-time.
*   **Multi-language Support:** Supports both English and Spanish.
*   **File Management:** Saves audio recordings as WAV files and maintains transcription logs in JSONL format.
*   **Configuration Panel:** A comprehensive settings panel to manage:
    *   Groq API Key
    *   File paths for audio and logs
    *   Recording hotkey (F1-F12)
    *   Default language
    *   File and log size limits
*   **System Tray Integration:** The application can be minimized to the system tray for unobtrusive operation.
*   **Production Mode:** A build script is included to create a production-ready version of the application that requires users to provide their own API key.

# Building and Running

## Prerequisites

*   Python 3.8+
*   A Groq API key

## Installation

1.  **Create a virtual environment:**

    ```bash
    python -m venv .venv
    ```

2.  **Activate the virtual environment:**

    ```bash
    # On Windows
    .venv\Scripts\activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

To run the application, execute the main script:

```bash
python audio2text_CENF_0.7.4.py
```

## Building for Production

The project includes a script to create a production-ready executable that does not contain a hardcoded API key.

1.  **Prepare for production:**

    ```bash
    python build_production.py
    ```

2.  **Build the executable:**

    ```bash
    pyinstaller --onefile audio2text_CENF_0.7.4_PRODUCCION.py --name "audio2text_CENF_PRODUCCION"
    ```

# Development Conventions

*   **Configuration:** Application settings are managed through a `config.json` file. A `ConfigManager` class is used to handle loading and saving the configuration.
*   **File Management:** A `FileManager` class is responsible for handling audio and log files, including saving, deleting, and size management.
*   **GUI:** The GUI is built using the `customtkinter` library, with a tabbed interface for the main application, settings, and information.
*   **Modularity:** The code is organized into classes for managing configuration, files, and sounds, promoting modularity and maintainability.
*   **Production vs. Development:** The application can be run in two modes:
    *   **Development Mode:** Uses a hardcoded API key for ease of testing.
    *   **Production Mode:** Requires the user to provide their own API key, ensuring security.
