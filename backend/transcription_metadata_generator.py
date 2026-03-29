"""
Transcription Metadata Generator - Genera metadatos automáticos con LLM.

Analiza la transcripción y extrae:
- Título sugerido
- Categoría
- Etiquetas
- Resumen corto
- Emojis sugeridos
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime


class TranscriptionMetadataGenerator:
    """Generador de metadatos automáticos para transcripciones."""

    def __init__(self, use_llm: bool = True):
        """
        Inicializar generador de metadatos.

        Args:
            use_llm: Si True, usa LLM para análisis profundo. Si False, usa reglas simples.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.use_llm = use_llm

        # Categorías predefinidas
        self.categories = {
            "trabajo": ["reunión", "llamada", "cliente", "proyecto", "tarea"],
            "idea": ["idea", "pensamiento", "innovación", "creatividad"],
            "personal": ["nota", "recordatorio", "personal", "casa"],
            "aprendizaje": ["tutorial", "curso", "explicación", "concepto"],
            "técnico": ["código", "bug", "feature", "implementación"],
        }

        # Emojis por categoría
        self.emoji_map = {
            "trabajo": ["💼", "📞", "📅", "📝", "✅"],
            "idea": ["💡", "✨", "🚀", "💫", "⚡"],
            "personal": ["🏠", "📌", "🔔", "📋", "⏰"],
            "aprendizaje": ["📚", "🎓", "💻", "🔬", "🧠"],
            "técnico": ["🔧", "⚙️", "💻", "🐛", "🔨"],
        }

    def generate_metadata(
        self,
        transcription: str,
        filename: str,
        use_llm: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Generar metadatos completos para una transcripción.

        Args:
            transcription: Texto de la transcripción
            filename: Nombre del archivo de audio
            use_llm: Sobrescribe la configuración de LLM

        Returns:
            Diccionario con metadatos generados
        """
        use_llm = use_llm if use_llm is not None else self.use_llm

        metadata = {
            "filename": filename,
            "generated_at": datetime.now().isoformat(),
            "transcription_length": len(transcription),
            "word_count": len(transcription.split()),
        }

        if use_llm:
            # Análisis profundo con LLM
            llm_metadata = self._generate_with_llm(transcription, filename)
            metadata.update(llm_metadata)
        else:
            # Análisis rápido con reglas
            rule_metadata = self._generate_with_rules(transcription, filename)
            metadata.update(rule_metadata)

        self.logger.info(f"Metadatos generados para {filename}: {metadata.get('category', 'desconocido')}")
        return metadata

    def _generate_with_llm(self, transcription: str, filename: str) -> Dict[str, Any]:
        """
        Generar metadatos usando LLM (Groq/OpenAI).

        Args:
            transcription: Texto de la transcripción
            filename: Nombre del archivo

        Returns:
            Metadatos generados por LLM
        """
        try:
            from groq import Groq
            from backend.config_manager import ConfigManager

            config = ConfigManager()
            api_key = config.get_groq_api_key_from_env()

            if not api_key:
                self.logger.warning("No API key de Groq disponible, usando reglas")
                return self._generate_with_rules(transcription, filename)

            client = Groq(api_key=api_key)

            # Prompt para análisis
            prompt = f"""Analiza esta transcripción y genera metadatos en formato JSON.

TRANSCRIPCIÓN:
{transcription[:1000]}  # Primeros 1000 caracteres

Genera un JSON con esta estructura exacta:
{{
    "title": "Título corto (máx 50 chars)",
    "category": "una de: trabajo, idea, personal, aprendizaje, técnico",
    "tags": ["tag1", "tag2", "tag3"],
    "summary": "Resumen de 1 oración (máx 100 chars)",
    "emoji": "un emoji representativo",
    "sentiment": "positivo, neutral o negativo",
    "action_items": ["acción1", "acción2"] si hay tareas,
    "mentions": ["persona1", "persona2"] si se mencionan nombres
}}

Responde SOLO con el JSON, nada más."""

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Modelo rápido y económico
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )

            result_text = response.choices[0].message.content.strip()

            # Limpiar respuesta (quitar markdown ```json si existe)
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            metadata = json.loads(result_text)
            metadata["method"] = "llm"

            return metadata

        except Exception as e:
            self.logger.error(f"Error generando metadatos con LLM: {e}")
            return self._generate_with_rules(transcription, filename)

    def _generate_with_rules(self, transcription: str, filename: str) -> Dict[str, Any]:
        """
        Generar metadatos usando reglas simples (sin LLM).

        Args:
            transcription: Texto de la transcripción
            filename: Nombre del archivo

        Returns:
            Metadatos generados por reglas
        """
        words = transcription.lower().split()
        word_count = len(words)

        # Detectar categoría por palabras clave
        category = "personal"
        detected_tags = []

        for cat_name, keywords in self.categories.items():
            if any(keyword in transcription.lower() for keyword in keywords):
                category = cat_name
                detected_tags = [kw for kw in keywords if kw in transcription.lower()][:3]
                break

        # Generar título desde primeras palabras
        first_words = " ".join(words[:5])
        title = f"{first_words.capitalize()}..." if word_count > 5 else first_words.capitalize()

        # Seleccionar emoji
        emojis = self.emoji_map.get(category, ["📝"])
        emoji = emojis[0]

        # Sentimiento simple
        positive_words = ["bien", "gracias", "excelente", "perfecto", "genial"]
        negative_words = ["mal", "error", "problema", "falla", "no funciona"]

        sentiment = "neutral"
        positive_count = sum(1 for w in positive_words if w in words)
        negative_count = sum(1 for w in negative_words if w in words)

        if positive_count > negative_count:
            sentiment = "positivo"
        elif negative_count > positive_count:
            sentiment = "negativo"

        # Resumen simple (primeras 2 oraciones)
        summary = " ".join(transcription.split(".")[:2]).strip()
        if len(summary) > 100:
            summary = summary[:97] + "..."

        metadata = {
            "title": title,
            "category": category,
            "tags": detected_tags[:3],
            "summary": summary,
            "emoji": emoji,
            "sentiment": sentiment,
            "action_items": [],
            "mentions": [],
            "method": "rules"
        }

        return metadata

    def generate_tooltip_text(self, metadata: Dict[str, Any]) -> str:
        """
        Generar texto formateado para tooltip.

        Args:
            metadata: Metadatos generados

        Returns:
            Texto formateado para mostrar en tooltip
        """
        lines = []

        if "title" in metadata:
            lines.append(f"📌 {metadata['title']}")

        if "category" in metadata:
            emoji_cat = metadata.get("emoji", "📝")
            lines.append(f"📂 {metadata['category'].capitalize()} {emoji_cat}")

        if "summary" in metadata:
            lines.append(f"📝 {metadata['summary']}")

        if "tags" in metadata and metadata["tags"]:
            tags_str = ", ".join(metadata["tags"][:3])
            lines.append(f"🏷️ {tags_str}")

        if "sentiment" in metadata:
            sentiment_emoji = {
                "positivo": "😊",
                "neutral": "😐",
                "negativo": "😟"
            }.get(metadata["sentiment"], "😐")
            lines.append(f"😊 {metadata['sentiment'].capitalize()} {sentiment_emoji}")

        if "action_items" in metadata and metadata["action_items"]:
            lines.append(f"✅ Acciones: {len(metadata['action_items'])}")

        return "\n".join(lines)


if __name__ == "__main__":
    # Test del generador
    generator = TranscriptionMetadataGenerator(use_llm=False)

    test_transcription = """
    Reunión con el equipo de desarrollo sobre el nuevo proyecto de Audio2Text.
    Discutimos la implementación del sistema de metadatos automáticos.
    Pablo sugirió usar LLM para generar títulos y resúmenes.
    Hay que implementar el análisis de sentimiento y extracción de tareas.
    """

    metadata = generator.generate_metadata(
        transcription=test_transcription,
        filename="audio_20260325_143022.wav"
    )

    print("Metadatos generados:")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

    print("\nTooltip:")
    print(generator.generate_tooltip_text(metadata))
