# -*- coding: utf-8 -*-
"""
Verificación: transcribir el WAV largo (296s) con trozado en silencios
y comparar contra la transcripción original (con truncados conocidos).

Este script NO usa la app — llama directo a la API de Groq vía chunker.
"""
import base64, json, sys, tempfile, time
from pathlib import Path
import numpy as np
import requests
import soundfile as sf

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from backend.audio_chunker import split_audio_on_silence, transcribe_chunks, MAX_WINDOW_S


def decode_gift_key(encoded):
    xor_key = "CENF_SECRET"
    decoded_bytes = base64.b64decode(encoded)
    return "".join(chr(b ^ ord(xor_key[i % len(xor_key)])) for i, b in enumerate(decoded_bytes))


def get_api_key():
    import os
    k = os.getenv("GROQ_API_KEY")
    if k: return k
    cfg = json.loads((REPO / "config.json").read_text(encoding="utf-8"))
    for f in ("groq_api_key", "gift_key_encoded"):
        if cfg.get(f): return decode_gift_key(cfg[f])
    raise SystemExit("No API key")


def call_groq_chunk(chunk, sr, prompt=None):
    """Escribe chunk a WAV temporal y lo manda a Groq."""
    tmp = Path(tempfile.mktemp(suffix=".wav"))
    try:
        sf.write(str(tmp), chunk, sr)
        api_key = get_api_key()
        with open(tmp, "rb") as f:
            files = {"file": (tmp.name, f, "audio/wav")}
            data = {
                "model": "whisper-large-v3",
                "response_format": "text",
                "language": "es",
                "temperature": "0",
            }
            if prompt:
                data["prompt"] = prompt
            r = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data,
                timeout=180,
            )
        if r.status_code != 200:
            print(f"  [HTTP {r.status_code}] {r.text[:200]}")
            return ""
        return r.text.strip()
    except Exception as e:
        print(f"  [ERR] {e}")
        return ""
    finally:
        tmp.unlink(missing_ok=True)


def main():
    src = REPO / "audio" / "audio_20260815_042105.wav"
    data, sr = sf.read(str(src))
    dur = len(data) / sr
    print(f"WAV: {src.name} | {dur:.1f}s | {len(data)} samples @ {sr}Hz")

    # Analizar chunks
    t0 = time.time()
    chunks = split_audio_on_silence(data, sr, target_s=25.0, max_s=29.0)
    print(f"\nTrozado: {len(chunks)} chunks en {time.time()-t0:.2f}s")
    for i, c in enumerate(chunks):
        print(f"  chunk {i:2d}: {len(c)/sr:5.1f}s ({len(c)} samples)")
    assert sum(len(c) for c in chunks) == len(data), "ERROR: samples perdidos en trozado"
    assert all(len(c) <= int(MAX_WINDOW_S * sr) + 1 for c in chunks), "ERROR: chunk supera ventana"
    print("✓ Invariantes: 0 samples perdidos, todos los chunks < 30s")

    # Transcribir con chunking
    print(f"\nTranscribiendo {len(chunks)} chunks con Groq (whisper-large-v3, temp=0)...")
    call_count = [0]
    def groq_cb(chunk, prompt=None):
        call_count[0] += 1
        txt = call_groq_chunk(chunk, sr, prompt)
        print(f"  chunk {call_count[0]:2d}/{len(chunks)}: {len(txt)} chars")
        return txt

    t0 = time.time()
    result = transcribe_chunks(data, sr, api_call=groq_cb, target_s=25.0, max_s=29.0)
    elapsed = time.time() - t0
    print(f"\nTranscripción completada en {elapsed:.1f}s ({call_count[0]} llamadas API)")
    print(f"Total: {len(result)} chars")

    # Comparar con transcripción original (con truncados)
    jsonl = REPO / "transcriptions" / "transcriptions_log.jsonl"
    entries = [json.loads(l) for l in jsonl.read_text(encoding="utf-8").strip().splitlines()]
    orig = [e for e in entries if "audio_20260815_042105" in (e.get("audio_file") or "")]
    orig_text = orig[0]["transcription"] if orig else ""

    # Patrones que ANTES estaban truncados
    truncados = [
        "modificaci ", "no s qu", "no s c ", "arranqu con",
        "Podr", "qu m", "grabaci ", "comunicaci ",
    ]
    completos = [
        "modificación", "no sé qué", "no sé cómo", "arranqué con",
        "Podría", "qué más", "grabación", "comunicación",
    ]

    print("\n=== COMPARACIÓN ===")
    print(f"{'Patrón':<20} {'ORIGINAL':<8} {'CHUNKED':<8}")
    for trunc, comp in zip(truncados, completos):
        in_orig = trunc in orig_text
        in_orig_comp = comp in orig_text
        in_new = trunc in result
        in_new_comp = comp in result
        orig_s = "❌ trunc" if in_orig else ("✅" if in_orig_comp else "—")
        new_s = "❌ trunc" if in_new else ("✅" if in_new_comp else "—")
        print(f"  {comp:<18} {orig_s:<8} {new_s}")

    # Guardar resultado
    out = REPO / "scripts" / "_chunked_result.txt"
    out.write_text(result, encoding="utf-8")
    orig_out = REPO / "scripts" / "_original_result.txt"
    orig_out.write_text(orig_text, encoding="utf-8")
    print(f"\nResultados guardados en scripts/_chunked_result.txt y _original_result.txt")

    # Conteo de truncados
    new_trunc = sum(1 for t in truncados if t in result)
    orig_trunc = sum(1 for t in truncados if t in orig_text)
    print(f"\nResumen: original tenía {orig_trunc} truncados, chunked tiene {new_trunc}")
    if new_trunc == 0:
        print("🎉 TODOS los truncados fueron eliminados por el trozado en silencios")
    elif new_trunc < orig_trunc:
        print(f"⚠️  Mejoría parcial: {orig_trunc - new_trunc} truncados eliminados de {orig_trunc}")
    else:
        print("❌ No hubo mejora")


if __name__ == "__main__":
    main()
