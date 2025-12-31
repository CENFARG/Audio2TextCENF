import winsound
import threading

class SoundManager:
    """Gestor de sonidos personalizados para la aplicación usando winsound"""

    def __init__(self):
        # Frecuencias en Hz para winsound.Beep
        self.frequencies = {
            "start": [(262, 100), (294, 100), (330, 100)],  # C4, D4, E4
            "stop": [(330, 100), (294, 100), (262, 100)],   # E4, D4, C4
            "error": [(150, 200)],
            "success": [(523, 80), (659, 80), (784, 80)]    # C5, E5, G5
        }

    def play_sound_sequence(self, sequence):
        """Reproducir secuencia de beeps en un thread separado"""
        def _play():
            try:
                for freq, duration in sequence:
                    winsound.Beep(freq, duration)
            except Exception as e:
                print(f"Error reproduciendo sonido: {e}")
        
        # Run in separate thread to avoid blocking
        threading.Thread(target=_play, daemon=True).start()

    def sound_start_recording(self):
        """Sonido de inicio de grabación (ascendente)"""
        self.play_sound_sequence(self.frequencies["start"])

    def sound_stop_recording(self):
        """Sonido de fin de grabación (descendente)"""
        self.play_sound_sequence(self.frequencies["stop"])

    def sound_error(self):
        """Sonido de error (frecuencia baja y disonante)"""
        self.play_sound_sequence(self.frequencies["error"])

    def sound_success(self):
        """Sonido de éxito (frecuencia alta y agradable)"""
        self.play_sound_sequence(self.frequencies["success"])

    def close(self):
        """Cerrar recursos de audio"""
        pass  # winsound no requiere limpieza
