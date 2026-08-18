import json
from pathlib import Path


FIXTURES = Path(__file__).parent / "fixtures"


def test_synthetic_fixtures_contain_no_secrets_or_machine_paths():
    config = json.loads((FIXTURES / "config_legacy_synthetic.json").read_text(encoding="utf-8"))
    audio = json.loads((FIXTURES / "audio_synthetic.json").read_text(encoding="utf-8"))

    assert not {"groq_api_key", "nvidia_api_key", "gift_key_encoded"} & config.keys()
    serialized = json.dumps({"config": config, "audio": audio})
    assert "C:\\" not in serialized
    assert "gsk_" not in serialized
    assert "nvapi-" not in serialized
    assert audio["sample_rate"] == 16000
    assert audio["samples"] == [0.0, 0.25, -0.25, 0.0, 0.125, -0.125]
