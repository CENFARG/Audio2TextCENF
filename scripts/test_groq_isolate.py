# -*- coding: utf-8 -*-
"""
Aislar la variable que dispara el bug de tildes truncadas:
- A) archivo COMPLETO + verbose_json
- B) archivo COMPLETO + text
- C) segmento 60s + text
"""
import json
from pathlib import Path
import requests
from test_groq_raw import get_api_key, carve, REPO

SRC = REPO / "audio" / "audio_20260815_042105.wav"
FULL = REPO / "audio" / "audio_20260815_042105.wav"


def transcribe(api_key, wav, model, response_format):
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}
    with open(wav, "rb") as f:
        files = {"file": (wav.name, f, "audio/wav")}
        data = {"model": model, "response_format": response_format, "language": "es", "temperature": "0"}
        r = requests.post(url, headers=headers, files=files, data=data, timeout=300)
    if r.status_code != 200:
        print(f"  [HTTP {r.status_code}] {r.text[:200]}")
        return None
    if response_format == "verbose_json":
        return r.json().get("text", "")
    return r.text


def check(text):
    if text is None:
        return
    trunc = [p for p in ("modificaci ", "no s qu", "no s c ", "históric"[:0] or "históric" + " ", "grabaci ", "comunicaci ") if p in text]
    comp = [p for p in ("modificación", "no sé qué", "no sé cómo", "mi historial") if p in text]
    print(f"  chars={len(text)} | TRUNCADOS={trunc} | COMPLETOS={comp}")
    # mostrar la frase clave con contexto
    for key in ("funcionar", "históric" if False else "historial"):
        i = text.find(key)
        if i >= 0:
            print(f"  ctx[{key!r}]: ...{text[max(0,i-80):i+60]}...")
            break


def main():
    api_key, _ = get_api_key()
    seg = carve(SRC, 150.0, 210.0)

    print("A) FULL 296s + verbose_json, whisper-large-v3")
    check(transcribe(api_key, FULL, "whisper-large-v3", "verbose_json"))

    print("B) FULL 296s + text, whisper-large-v3")
    check(transcribe(api_key, FULL, "whisper-large-v3", "text"))

    print("C) SEG 60s + text, whisper-large-v3")
    check(transcribe(api_key, seg, "whisper-large-v3", "text"))


if __name__ == "__main__":
    main()
