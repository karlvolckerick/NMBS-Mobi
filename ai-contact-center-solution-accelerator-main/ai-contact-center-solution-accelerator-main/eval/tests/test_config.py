import pytest
import yaml

from eval.config import load_eval_config


class TestLoadEvalConfig:
    def test_load_minimal_config(self, sample_config_path):
        config = load_eval_config(sample_config_path)

        assert config.target.endpoint == "ws://localhost:8000/ws"
        assert config.azure_openai.chat_deployment == "gpt-4o"
        assert config.dataset == "scenarios.jsonl"
        assert config.conversation.max_turns == 15
        assert config.execution.concurrency == 1

    def test_load_config_with_overrides(self, tmp_config_dir):
        config_data = {
            "target": {"endpoint": "ws://remote:9000/ws", "headers": {"Authorization": "Bearer token"}},
            "azure_openai": {
                "endpoint": "https://test.openai.azure.com/",
                "chat_deployment": "gpt-4o",
                "tts_deployment": "tts",
                "transcription_deployment": "transcribe",
            },
            "dataset": "custom.jsonl",
            "conversation": {"max_turns": 10, "voice": "nova"},
            "execution": {"concurrency": 4, "output_dir": "custom_output"},
        }
        config_path = tmp_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        config = load_eval_config(config_path)
        assert config.target.headers == {"Authorization": "Bearer token"}
        assert config.conversation.max_turns == 10
        assert config.conversation.voice == "nova"
        assert config.execution.concurrency == 4

    def test_config_not_found(self, tmp_config_dir):
        with pytest.raises(FileNotFoundError):
            load_eval_config(tmp_config_dir / "nonexistent.yaml")

    def test_env_var_expansion(self, tmp_config_dir, monkeypatch):
        monkeypatch.setenv("TEST_ENDPOINT", "ws://expanded:8000/ws")
        config_data = {
            "target": {"endpoint": "${TEST_ENDPOINT}"},
            "azure_openai": {
                "endpoint": "https://test.openai.azure.com/",
                "chat_deployment": "gpt-4o",
                "tts_deployment": "tts",
                "transcription_deployment": "transcribe",
            },
            "dataset": "scenarios.jsonl",
        }
        config_path = tmp_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        config = load_eval_config(config_path)
        assert config.target.endpoint == "ws://expanded:8000/ws"
