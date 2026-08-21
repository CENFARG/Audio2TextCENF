"""
Custom Vocabulary - Corrección de palabras mal entendidas

Permite agregar palabras que el modelo de transcripción tiende a entender mal,
como "CENF" que se transcribe como "zenf", "cemp", "cemf", etc.

Author: Audio2Text Development Team
Version: 0.11.0
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class CustomVocabulary:
    """
    Gestor de vocabulario personalizado para correcciones.

    Permite definir correcciones para palabras que el modelo entiende mal.
    """

    def __init__(self, vocab_path: str = "backend/vocabulary/custom_corrections.json"):
        """
        Inicializar gestor de vocabulario personalizado.

        Args:
            vocab_path: Ruta al archivo de correcciones
        """
        self.vocab_path = Path(vocab_path)
        self.corrections: Dict[str, str] = {}
        self._load_vocab()

    def _load_vocab(self):
        """Cargar correcciones desde archivo."""
        if self.vocab_path.exists():
            try:
                with open(self.vocab_path, 'r', encoding='utf-8') as f:
                    self.corrections = json.load(f)
                logger.info(f"Correcciones cargadas: {len(self.corrections)} términos")
            except Exception as e:
                logger.error(f"Error cargando correcciones: {e}")
                self.corrections = {}
        else:
            # Crear con ejemplos por defecto
            self.corrections = {
                "zenf": "CENF",
                "cemp": "CENF",
                "cemf": "CENF",
                "senf": "CENF",
                "gro": "Groq",
                "grog": "Groq"
            }
            self._save_vocab()

    def _save_vocab(self):
        """Guardar correcciones a archivo."""
        try:
            self.vocab_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.vocab_path, 'w', encoding='utf-8') as f:
                json.dump(self.corrections, f, indent=4, ensure_ascii=False)
            logger.info(f"Correcciones guardadas: {len(self.corrections)} términos")
        except Exception as e:
            logger.error(f"Error guardando correcciones: {e}")

    def add_correction(self, incorrect: str, correct: str) -> bool:
        """
        Agregar corrección al vocabulario.

        FIX: respetar el caso EXACTO tal como se define (CENF, amBotHs, etc.).
        Antes se guardaba la clave en minúsculas (incorrect.lower()) y la
        corrección se aplicaba según el caso del texto transcrito, destruyendo
        el caso definido por el usuario.

        Args:
            incorrect: Palabra incorrecta que el modelo usa
            correct: Palabra correcta que debería ser

        Returns:
            True si se agregó exitosamente
        """
        try:
            # Mantener el caso EXACTO de la clave y del valor definidos por el usuario
            self.corrections[incorrect] = correct
            self._save_vocab()
            logger.info(f"Corrección agregada: '{incorrect}' → '{correct}'")
            return True
        except Exception as e:
            logger.error(f"Error agregando corrección: {e}")
            return False

    def remove_correction(self, incorrect: str) -> bool:
        """
        Eliminar corrección del vocabulario.

        FIX: la búsqueda debe ser case-insensitive pero borrar la clave real
        (que puede tener cualquier caso).
        """
        try:
            for key in list(self.corrections.keys()):
                if key.lower() == incorrect.lower():
                    del self.corrections[key]
                    self._save_vocab()
                    logger.info(f"Corrección eliminada: '{key}'")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error eliminando corrección: {e}")
            return False

    def get_corrections(self) -> Dict[str, str]:
        """Obtener todas las correcciones."""
        return self.corrections.copy()

    def import_from_text(self, text: str, fmt: str = "auto") -> int:
        """
        Importar correcciones desde texto (TXT/MD/JSON).

        Formatos soportados:
        - "lineas": una equivalencia por línea:  "incorrecta → correcta"
          o "incorrecta -> correcta" o "incorrecta=correcta" o "incorrecta: correcta"
          (las líneas que empiecen con #, // o ; se ignoran como comentarios)
        - "json": objeto {"incorrecta": "correcta", ...}
        - "auto": detecta JSON si el texto empieza con '{', si no usa líneas

        Args:
            text: Contenido del archivo/texto
            fmt: Formato ("auto", "lineas" o "json")

        Returns:
            Cantidad de correcciones importadas
        """
        import json as _json

        fmt = fmt or "auto"
        content = (text or "").strip()
        if not content:
            return 0

        if fmt == "auto":
            fmt = "json" if content.startswith('{') else "lineas"

        nuevos = {}
        if fmt == "json":
            try:
                data = _json.loads(content)
                if not isinstance(data, dict):
                    logger.error("Import: el JSON debe ser un objeto {incorrecta: correcta}")
                    return 0
                for k, v in data.items():
                    k = str(k).strip()
                    v = str(v).strip()
                    if k and v:
                        nuevos[k] = v
            except Exception as e:
                logger.error(f"Import: error parseando JSON: {e}")
                return 0
        else:
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith(('#', '//', ';')):
                    continue
                # Separadores soportados
                sep = None
                for candidate in ('→', '->', '=', ':'):
                    if candidate in line:
                        sep = candidate
                        break
                if not sep:
                    continue
                incorrect = line.split(sep, 1)[0].strip()
                correct = line.split(sep, 1)[1].strip()
                if incorrect and correct:
                    nuevos[incorrect] = correct

        if nuevos:
            self.corrections.update(nuevos)
            self._save_vocab()
            logger.info(f"Import: {len(nuevos)} correcciones importadas")
        return len(nuevos)

    def import_from_file(self, file_path: str) -> int:
        """
        Importar correcciones desde un archivo (.txt, .md, .json).

        Args:
            file_path: Ruta al archivo

        Returns:
            Cantidad de correcciones importadas
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Import: no existe el archivo {file_path}")
            return 0

        ext = path.suffix.lower()
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = path.read_text(encoding='latin-1')

        fmt = "json" if ext == ".json" else "lineas"
        return self.import_from_text(content, fmt=fmt)

    def export_to_file(self, file_path: str) -> bool:
        """
        Exportar el vocabulario actual de forma DETERMINÍSTICA.

        - .txt / .md : líneas  incorrecta=correcta  (sin espacios, con =)
                       respeta el caso exacto tal como lo escribió el usuario
        - .json      : objeto JSON  {incorrecta: correcta}

        Determinista: no infiere, no usa IA, case-sensitive exacto.

        Args:
            file_path: Ruta de destino

        Returns:
            True si se exportó correctamente
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            ext = path.suffix.lower()
            if ext == ".json":
                # JSON determinista: objeto directo, ensure_ascii=False, indent=2
                import json as _json
                path.write_text(_json.dumps(self.corrections, ensure_ascii=False, indent=2), encoding='utf-8')
            else:
                # TXT/MD: formato  incorrecta=correcta  sin espacios
                lines = [f"{k}={v}" for k, v in self.corrections.items()]
                path.write_text("\n".join(lines), encoding='utf-8')
            logger.info(f"Export: {len(self.corrections)} correcciones exportadas a {file_path} ({ext or 'txt'})")
            return True
        except Exception as e:
            logger.error(f"Export: error {e}")
            return False

    def apply_corrections(self, text: str) -> str:
        """
        Aplicar correcciones a un texto.

        FIX mayúsculas: se respeta el caso EXACTO definido en el vocabulario, SIEMPRE.
        - Si se definió "CENF" -> se escribe "CENF" (no "cenf")
        - Si se definió "amBotHs" -> se escribe "amBotHs" (no "AMBOTHS" ni "amboths")
          incluso si el modelo la transcribió en mayúsculas o al inicio de oración.

        Args:
            text: Texto a corregir

        Returns:
            Texto con correcciones aplicadas
        """
        if not text or not self.corrections:
            return text

        corrected_text = text
        corrections_applied = []

        for incorrect, correct in self.corrections.items():
            # Buscar y reemplazar la palabra incorrecta
            # Usamos word boundaries para no reemplazar dentro de otras palabras
            import re

            # Crear patrón con word boundary (case-insensitive para encontrar
            # cualquier variante de caso que haya escrito el modelo)
            pattern = r'\b' + re.escape(incorrect) + r'\b'

            # Buscar todas las ocurrencias (case-insensitive)
            matches = list(re.finditer(pattern, corrected_text, re.IGNORECASE))

            if matches:
                # Procesar cada ocurrencia individualmente
                # Procesar de derecha a izquierda para no afectar los índices
                for match in reversed(matches):
                    matched_text = match.group()
                    start, end = match.span()

                    # FIX: reemplazo SIEMPRE con el caso definido por el usuario.
                    # Sin derivaciones por el caso del texto transcrito.
                    replacement = correct
                    corrected_text = corrected_text[:start] + replacement + corrected_text[end:]
                    corrections_applied.append(f"{matched_text} → {replacement}")

        if corrections_applied:
            logger.info(f"Correcciones aplicadas: {corrections_applied}")

        return corrected_text

    def get_whisper_prompt(self) -> str:
        """
        Generar un prompt para Whisper con las palabras correctas.

        Whisper usa el prompt para mejorar la transcripción de palabras específicas.
        Incluimos las palabras CORRECTAS (no las incorrectas) para ayudar al modelo.

        Returns:
            String con palabras correctas separadas por comas
        """
        if not self.corrections:
            return ""

        # Obtener palabras únicas correctas
        correct_words = set(self.corrections.values())

        # Crear prompt contextual
        # Whisper funciona mejor con frases contextuales
        prompts = []
        for word in correct_words:
            if word == "CENF":
                prompts.append("CENF es una empresa de tecnología")
            elif word == "Groq":
                prompts.append("Groq es una plataforma de inferencia AI")
            else:
                prompts.append(word)

        return ". ".join(prompts) + "."

    def get_stats(self) -> Dict[str, any]:
        """Obtener estadísticas del vocabulario."""
        return {
            'total_corrections': len(self.corrections),
            'corrections': self.corrections.copy()
        }
