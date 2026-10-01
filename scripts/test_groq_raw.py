# -*- coding: utf-8 -*-
"""
Test decisivo: enviar el MISMO segmento de audio directo a la API de Groq
(sin pasar por la app) para ver si los truncados de tildes ("modificaci",
"no s qu") están en la respuesta CRUDA del modelo o se generan en la app.

Uso: python scripts/test_groq_raw.py
"""
import base64
import json
import sys
import tempfile
from pathlib import Path

import soundfile as sf
import requests

REPO = Path(__file__).resolve().parent.parent


def decode_gift_key(encoded: str) -> str:
    xor_key = "CENF_SECRET"
    decoded_bytes = base64.b64decode(encoded)
    return "".join(chr(b ^ ord(xor_key[i % len(xor_key)])) for i, b in enumerate(decoded_bytes))


def get_api_key():
    # 1) env
    import os
    k = os.getenv("GROQ_API_KEY")
    if k:
        return k, "env"
    # 2) config.json (ofuscada)
    cfg = json.loads((REPO / "config.json").read_text(encoding="utf-8"))
    for field in ("groq_api_key", "gift_key_encoded"):
        if cfg.get(field):
            return decode_gift_key(cfg[field]), f"config:{field}"
    raise SystemExit("No hay API key disponible")


def carve(src: Path, t0: float, t1: float) -> Path:
    data, sr = sf.read(src)
    seg = data[int(t0 * sr):int(t1 * sr)]
    out = Path(tempfile.gettempdir()) / f"a2t_seg_{int(t0)}_{int(t1)}.wav"
    sf.write(out, seg, sr)
    return out


def transcribe(api_key: str, wav: Path, model: str, response_format: str):
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}
    with open(wav, "rb") as f:
        files = {"file": (wav.name, f, "audio/wav")}
        data = {"model": model, "response_format": response_format, "language": "es", "temperature": "0"}
        r = requests.post(url, headers=headers, files=files, data=data, timeout=180)
    if r.status_code != 200:
        print(f"  [HTTP {r.status_code}] {r.text[:300]}")
        return None
    return r.json() if response_format == "verbose_json" else {"text": r.text}


def main():
    t0, t1 = 150.0, 210.0
    src = REPO / "audio" / "audio_20260815_042105.wav"
    print(f"Recortando {src.name} [{t0}s - {t1}s] ...")
    seg = carve(src, t0, t1)
    print(f"Segmento: {seg} ({seg.stat().st_size/1e6:.1f} MB)")

    api_key, src_key = get_api_key()
    print(f"API key obtenida de: {src_key} ({api_key[:6]}...)")

    for model in ("whisper-large-v3", "whisper-large-v3-turbo"):
        print(f"\n=== MODELO: {model} (temperature=0, verbose_json) ===")
        res = transcribe(api_key, seg, model, "verbose_json")
        if not res:
            continue
        text = res.get("text", "")
        print(f"chars: {len(text)} | segmentos: {len(res.get('segments', []))}")
        print("TEXT:", text[:1200])
        # chequear patrones
        truncados = ["modificaci", "no s qu", "grabaci ", "comunicaci ", "Est cometiendo", "inici "]
        completos = ["modificación", "no sé qué", "grabación", "comunicación", "está cometiendo"]
        print("\nPatrones TRUNCADOS presentes:", [p for p in truncados if p in text])
        print("Patrones COMPLETOS presentes:", [p for p in completos if p in text])
        # dump de segmentos para inspección
        segfile = REPO / f"scripts/_raw_{model.replace('/', '_')}.json"
        segfile.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"(respuesta completa en {segfile})")


if __name__ == "__main__":
    main()
