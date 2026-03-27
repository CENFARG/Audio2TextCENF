#!/usr/bin/env python3
"""Script para corregir problemas de UI en Flet."""
import re

# Leer el archivo
with open("ui_flet/main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Reemplazos masivos
replacements = [
    # Eliminar style=DesignSystem.TYPOGRAPHY
    (r'style=DesignSystem\.TYPOGRAPHY\["heading_large"\]', 'size=20, weight=ft.FontWeight.BOLD, color="#F8FAFC"'),
    (r'style=DesignSystem\.TYPOGRAPHY\["heading_medium"\]', 'size=16, weight=ft.FontWeight.BOLD, color="#F8FAFC"'),
    (r'style=DesignSystem\.TYPOGRAPHY\["body_medium"\]', 'size=14, color="#F8FAFC"'),
    (r'style=DesignSystem\.TYPOGRAPHY\["body_small"\]', 'size=12, color="#CBD5E1"'),
    (r'style=DesignSystem\.TYPOGRAPHY\["link"\]', 'size=12, color="#2563EB"'),

    # Eliminar style= cuando tiene TextStyle
    (r', style=ft\.TextStyle\([^)]+\)', ''),

    # Localized strings conocidos
    (r'self\.localization\.get_string\("settings_title_main"\)', '"Configuración Principal"'),
    (r'self\.localization\.get_string\("api_key_placeholder"\)', '"API Key de Groq"'),
    (r'self\.localization\.get_string\("verify_button"\)', '"Verificar"'),
    (r'self\.localization\.get_string\("hotkey_label"\)', '"Hotkey de Grabación"'),
    (r'self\.localization\.get_string\("record_hotkey_button"\)', '"Grabar Hotkey"'),
    (r'self\.localization\.get_string\("record_mode_label"\)', '"Modo de Grabación"'),
    (r'self\.localization\.get_string\("record_mode_toggle"\)', '"Toggle"'),
    (r'self\.localization\.get_string\("record_mode_hold"\)', '"Mantener Presionado"'),
    (r'self\.localization\.get_string\("auto_paste_switch"\)', '"Auto-pegar texto"'),
    (r'self\.localization\.get_string\("show_panel_switch"\]', '"Mostrar panel de transcripción"'),
    (r'self\.localization\.get_string\("autostart_windows_switch"\)', '"Iniciar con Windows"'),
    (r'self\.localization\.get_string\("language_label"\)', '"Idioma"'),
    (r'self\.localization\.get_string\("settings_title_files"\)', '"Archivos"'),
    (r'self\.localization\.get_string\("audio_path_label"\)', '"Carpeta de Audio"'),
    (r'self\.localization\.get_string\("transcriptions_path_label"\)', '"Carpeta de Transcripciones"'),
    (r'self\.localization\.get_string\("save_audio_switch"\)', '"Guardar audio"'),
    (r'self\.localization\.get_string\("save_logs_switch"\)', '"Guardar transcripciones"'),
    (r'self\.localization\.get_string\("history_title"\)', '"Historial de Grabaciones"'),
    (r'self\.localization\.get_string\("refresh_button"\)', '"Refrescar"'),
    (r'self\.localization\.get_string\("no_audio_files"\)', '"No hay archivos de audio"'),
    (r'self\.localization\.get_string\("transcribe_button"\)', '"Transcribir"'),
    (r'self\.localization\.get_string\("groq_api_key_link"\)', '"Obtener API Key"'),
    (r'self\.localization\.get_string\("info_text_simplified"[^)]*\)', '"Audio2Text v0.10.0 - Transcribe audio con IA"'),
    (r'self\.localization\.get_string\("cenf_website"\)', '"Audio2Text CENF"'),
    (r'self\.localization\.get_string\("tab_main"\)', '"Principal"'),
    (r'self\.localization\.get_string\("tab_settings"\)', '"Configuración"'),
    (r'self\.localization\.get_string\("tab_info"\)', '"Info"'),
    (r'self\.localization\.get_string\("tab_history"\)', '"Historial"'),
    (r'self\.localization\.get_string\("tab_updates"\)', '"Actualizaciones"'),
]

# Aplicar reemplazos
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Guardar el archivo
with open("ui_flet/main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Archivo corregido exitosamente!")
