@echo off
echo === Starting Audio2Text v0.11.0 Build ===
echo Time: %time%
echo.

cd /d "C:\Dropbox\DOC.RECA\06-Software\Audio2Text"

"C:\Program Files\Python312\python.exe" -m PyInstaller --onefile --windowed --clean --noconfirm --name=Audio2Text_CENF_0.11.0 --noupx --add-data "lang;lang" --add-data "config.json;." --add-data "assets\icons\icono.ico;assets/icons" --add-data "assets\logos\logo.png;assets/logos" --add-data "templates\info_template.html;templates" --hidden-import flet --hidden-import flet.runtime --collect-all flet --hidden-import PIL --hidden-import PIL._imagingtk --hidden-import sounddevice --hidden-import soundfile --hidden-import mouse --hidden-import keyboard --hidden-import pyautogui --hidden-import pyperclip --hidden-import psutil --hidden-import groq --hidden-import requests --hidden-import backend.blocks --hidden-import backend.blocks.base_block --hidden-import backend.blocks.block_manager --hidden-import backend.blocks.task_extractor_block --hidden-import backend.blocks.summary_block --hidden-import backend.blocks.keyword_extractor_block --hidden-import backend.custom_vocabulary --exclude-module pandas --exclude-module yt_dlp --exclude-module tkinter --exclude-module customtkinter --distpath="scripts\dist" --workpath="scripts\build" --icon="assets\icons\icono.ico" --version-file="config\version_info.txt" main.py

echo.
echo === Build Complete ===
echo Exit Code: %errorlevel%
if %errorlevel% equ 0 (
    echo SUCCESS!
    dir "scripts\dist\*.exe"
) else (
    echo FAILED!
)
echo.
echo Time: %time%
