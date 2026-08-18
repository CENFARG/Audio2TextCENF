"""
Unit tests para CustomVocabulary — FIX v0.15.0.

Documenta las correcciones:
- Case: respetar mayúsculas/minúsculas tal como se define (CENF, amBotHs)
- Import: importar desde texto (TXT/MD/JSON) y desde archivo
- Export: exportar vocabulario a archivo

Author: Audio2Text Development Team
Version: 0.15.0
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.custom_vocabulary import CustomVocabulary


@pytest.mark.unit
class TestCustomVocabularyCase:
    """Tests de respeto de mayúsculas/minúsculas (bug reportado por usuario)."""

    def setup_method(self):
        self.vocab = CustomVocabulary(vocab_path="backend/vocabulary/test_case.json")
        self.vocab.corrections = {}

    def teardown_method(self):
        import os
        try:
            os.remove("backend/vocabulary/test_case.json")
        except OSError:
            pass

    def test_add_correction_preserva_caso_incorrect(self):
        """add_correction debe guardar la clave con el caso EXACTO definido."""
        self.vocab.add_correction("zenf", "CENF")
        assert "zenf" in self.vocab.corrections
        assert self.vocab.corrections["zenf"] == "CENF"

    def test_add_correction_preserva_caso_correct(self):
        """El valor correcto debe quedar tal cual se define (CENF, amBotHs)."""
        self.vocab.add_correction("zenf", "CENF")
        self.vocab.add_correction("ambots", "amBotHs")
        assert self.vocab.corrections["zenf"] == "CENF"
        assert self.vocab.corrections["ambots"] == "amBotHs"

    def test_apply_corrections_respeta_caso_CENF(self):
        """'zenf' transcrito en minúsculas debe convertirse en 'CENF' (definido)."""
        self.vocab.corrections = {"zenf": "CENF"}
        result = self.vocab.apply_corrections("trabajo con zenf todos los días")
        assert result == "trabajo con CENF todos los días"

    def test_apply_corrections_respeta_caso_amBotHs(self):
        """'ambots' debe convertirse en 'amBotHs' exacto, no 'AMBOTHS' ni 'amboths'."""
        self.vocab.corrections = {"ambots": "amBotHs"}
        result = self.vocab.apply_corrections("el agente ambots está activo")
        assert result == "el agente amBotHs está activo"

    def test_apply_corrections_caso_mezclado_transcrito(self):
        """Incluso si el modelo escribe la palabra en mayúsculas, se respeta el definido."""
        self.vocab.corrections = {"ambots": "amBotHs"}
        result = self.vocab.apply_corrections("AMBOTS está escuchando")
        assert result == "amBotHs está escuchando"

    def test_apply_corrections_inicio_oracion_respeta_caso(self):
        """Al inicio de oración también se respeta el caso definido (amBotHs, no AmBotHs)."""
        self.vocab.corrections = {"ambots": "amBotHs"}
        result = self.vocab.apply_corrections("Ambots escucha reuniones.")
        assert result == "amBotHs escucha reuniones."

    def test_remove_correction_case_insensitive(self):
        """remove debe borrar sin importar el caso de la clave."""
        self.vocab.corrections = {"zenf": "CENF", "ambots": "amBotHs"}
        assert self.vocab.remove_correction("ZENF") is True
        assert "zenf" not in self.vocab.corrections


@pytest.mark.unit
class TestCustomVocabularyImport:
    """Tests de importación de vocabulario desde texto/archivo."""

    def setup_method(self):
        self.vocab = CustomVocabulary(vocab_path="backend/vocabulary/test_import.json")
        self.vocab.corrections = {}

    def teardown_method(self):
        import os
        for f in ["backend/vocabulary/test_import.json", "backend/vocabulary/vocab_test.txt"]:
            try:
                os.remove(f)
            except OSError:
                pass

    def test_import_lineas_con_flecha(self):
        """Importar desde texto con separador →."""
        text = "zenf → CENF\nambots → amBotHs\ngrog → Groq"
        count = self.vocab.import_from_text(text, fmt="lineas")
        assert count == 3
        assert self.vocab.corrections["zenf"] == "CENF"
        assert self.vocab.corrections["ambots"] == "amBotHs"

    def test_import_lineas_con_arrow_y_equals(self):
        """Soportar también -> y = como separadores."""
        text = "zenf -> CENF\nambots=amBotHs"
        count = self.vocab.import_from_text(text, fmt="lineas")
        assert count == 2

    def test_import_ignora_comentarios_y_vacias(self):
        """Ignorar líneas de comentario (#, //, ;) y vacías."""
        text = "# comentario\n\nzenf → CENF\n// otro comentario\n; y otro\nambots → amBotHs"
        count = self.vocab.import_from_text(text, fmt="lineas")
        assert count == 2

    def test_import_json(self):
        """Importar desde JSON dict."""
        data = json.dumps({"zenf": "CENF", "ambots": "amBotHs"})
        count = self.vocab.import_from_text(data, fmt="json")
        assert count == 2

    def test_import_json_auto_detectado(self):
        """fmt='auto' debe detectar JSON por el primer carácter '{'."""
        data = json.dumps({"zenf": "CENF"})
        count = self.vocab.import_from_text(data, fmt="auto")
        assert count == 1

    def test_import_archivo_txt(self, tmp_path):
        """Importar desde archivo .txt."""
        f = tmp_path / "vocab.txt"
        f.write_text("zenf → CENF\nambots → amBotHs\n", encoding="utf-8")
        count = self.vocab.import_from_file(str(f))
        assert count == 2

    def test_import_archivo_json(self, tmp_path):
        """Importar desde archivo .json."""
        f = tmp_path / "vocab.json"
        f.write_text(json.dumps({"zenf": "CENF"}), encoding="utf-8")
        count = self.vocab.import_from_file(str(f))
        assert count == 1

    def test_export_archivo(self, tmp_path):
        """Exportar vocabulario a archivo .txt."""
        self.vocab.corrections = {"zenf": "CENF", "ambots": "amBotHs"}
        out = tmp_path / "out.txt"
        assert self.vocab.export_to_file(str(out)) is True
        content = out.read_text(encoding="utf-8")
        assert "zenf → CENF" in content
        assert "ambots → amBotHs" in content

    def test_import_respeto_caso(self):
        """Importar respeta el caso de las palabras definidas."""
        self.vocab.import_from_text("zenf → CENF\nambots → amBotHs", fmt="lineas")
        assert self.vocab.corrections["zenf"] == "CENF"
        assert self.vocab.corrections["ambots"] == "amBotHs"
