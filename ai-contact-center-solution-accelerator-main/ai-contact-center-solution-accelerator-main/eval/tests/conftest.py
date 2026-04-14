from pathlib import Path

import pytest
import yaml


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def sample_config_data():
    return {
        "target": {"endpoint": "ws://localhost:8000/ws"},
        "azure_openai": {
            "endpoint": "https://test.openai.azure.com/",
            "chat_deployment": "gpt-4o",
            "tts_deployment": "gpt-4o-mini-tts",
            "transcription_deployment": "gpt-4o-transcribe",
        },
        "dataset": "scenarios.jsonl",
    }


@pytest.fixture
def sample_config_path(tmp_config_dir, sample_config_data):
    config_path = tmp_config_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(sample_config_data, f)
    return config_path
