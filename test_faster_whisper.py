"""
Script de prueba para faster-whisper

Prueba la transcripción con diferentes modelos y dispositivos.
"""

import sys
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_faster_whisper():
    """Probar faster-whisper con modelo base."""
    try:
        from faster_whisper import WhisperModel
        logger.info("✅ faster-whisper instalado correctamente")

        # Probar con modelo tiny (más rápido para descargar)
        logger.info("🔄 Descargando/verificando modelo 'tiny'...")
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        logger.info("✅ Modelo 'tiny' cargado exitosamente")

        # Información del modelo
        logger.info(f"📊 Modelo: tiny")
        logger.info(f"📊 Dispositivo: CPU")
        logger.info(f"📊 Compute type: int8")

        # Crear audio de prueba (1 segundo de silencio)
        import tempfile
        import numpy as np
        import soundfile as sf

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_audio = f.name

        # Generar 1 segundo de audio aleatorio
        sample_rate = 16000
        duration = 1  # segundos
        audio_data = np.random.uniform(-1, 1, int(sample_rate * duration)).astype(np.float32)
        sf.write(temp_audio, audio_data, sample_rate)

        logger.info(f"🎵 Audio de prueba creado: {temp_audio}")

        # Transcribir
        logger.info("🔄 Probando transcripción...")
        segments, info = model.transcribe(
            temp_audio,
            language="es",
            beam_size=5,
            vad_filter=True
        )

        # Recolectar transcripción
        transcript_parts = []
        for segment in segments:
            if segment.text:
                transcript_parts.append(segment.text.strip())

        full_transcript = " ".join(transcript_parts).strip()

        logger.info(f"✅ Transcripción completada: '{full_transcript}' (vacío es normal para audio aleatorio)")
        logger.info(f"📊 Duración detectada: {info.duration:.2f}s")
        logger.info(f"📊 Idioma detectado: {info.language} (probabilidad: {info.language_probability:.2f})")

        # Limpiar
        import os
        if os.path.exists(temp_audio):
            os.unlink(temp_audio)

        logger.info("✅ Prueba completada exitosamente")

        # Mostrar información sobre modelos disponibles
        logger.info("\n📦 Modelos disponibles en faster-whisper:")
        models = {
            "tiny": "39M - Más rápido (~1GB RAM)",
            "base": "74M - Rápido (~1GB RAM)",
            "small": "244M - Balanceado (~2GB RAM)",
            "medium": "769M - Preciso (~5GB RAM)",
            "large-v3": "1550M - Máxima precisión (~10GB RAM)"
        }
        for model_name, description in models.items():
            logger.info(f"   • {model_name:12s}: {description}")

        logger.info("\n💡 Recomendación:")
        logger.info("   • Para pruebas rápidas: tiny")
        logger.info("   • Para uso diario: base o small")
        logger.info("   • Para máxima precisión: large-v3 (igual que Groq)")

        return True

    except ImportError as e:
        logger.error(f"❌ Error importando faster-whisper: {e}")
        logger.info("💡 Instala con: pip install faster-whisper")
        return False
    except Exception as e:
        logger.error(f"❌ Error en prueba: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TEST: faster-whisper para Audio2Text")
    print("=" * 60)
    print()

    success = test_faster_whisper()

    print()
    print("=" * 60)
    if success:
        print("✅ TEST EXITOSO - faster-whisper funcionando correctamente")
        print("✅ Puedes usar faster-whisper en Audio2Text")
    else:
        print("❌ TEST FALLÓ - Revisa los errores arriba")
        sys.exit(1)
    print("=" * 60)
