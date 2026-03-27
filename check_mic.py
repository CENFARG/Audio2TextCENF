#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para verificar dispositivos de audio y micrófono"""
import sounddevice as sd

print("=" * 60)
print("DIAGNOSTICO DE MICROFONO")
print("=" * 60)

print("\n[+] Dispositivos de entrada (microfonos):")
devices = sd.query_devices(kind='input')
for i in range(len(devices)):
    try:
        name = devices[i]['name']
        if name:
            is_default = " [DEFAULT]" if devices[i].get('default_samplerate', 0) > 0 else ""
            print(f"  [{i}] {name}{is_default}")
    except:
        pass

print("\n[+] SOLUCIONES:")
print("1. Cierra Chrome, Edge, Teams, Zoom, WhatsApp Web")
print("2. Verifica: Configuracion Windows -> Sonido -> Grabar")
print("3. Verifica: Configuracion Windows -> Privacidad -> Micrófono")
print("4. Reinicia Audio2Text")
print("=" * 60)
