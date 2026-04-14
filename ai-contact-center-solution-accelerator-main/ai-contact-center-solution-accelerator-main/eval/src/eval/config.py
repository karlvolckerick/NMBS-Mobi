import os
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


def _expand_env_vars(value):
    """Recursively expand ${ENV_VAR} patterns in config values."""
    if isinstance(value, str):
        return re.sub(
            r"\$\{(\w+)\}",
            lambda m: os.environ.get(m.group(1), m.group(0)),
            value,
        )
    if isinstance(value, dict):
        return {k: _expand_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_vars(item) for item in value]
    return value


class TargetConfig(BaseModel):
    endpoint: str = Field(..., description="WebSocket endpoint URL")
    headers: dict[str, str] = Field(default_factory=dict, description="Optional headers for WebSocket connection")


class AzureOpenAIConfig(BaseModel):
    endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    api_version: str = Field(default="2025-04-01-preview", description="API version")
    chat_deployment: str = Field(..., description="Chat deployment for customer LLM and evaluator judge")
    tts_deployment: str = Field(..., description="TTS deployment for text-to-speech")
    transcription_deployment: str = Field(..., description="Transcription deployment for speech-to-text")


class ConversationConfig(BaseModel):
    max_turns: int = Field(default=15, description="Max customer-agent exchanges")
    voice: str = Field(default="alloy", description="TTS voice for simulated customer")
    greeting_wait_seconds: float = Field(default=5, description="Wait time for agent greeting")
    silence_timeout_seconds: float = Field(default=10, description="Max silence before assuming agent is done")


class ExecutionConfig(BaseModel):
    concurrency: int = Field(default=1, description="Number of parallel scenarios")
    output_dir: str = Field(default="outputs", description="Output directory for results")


class EvalConfig(BaseModel):
    target: TargetConfig
    azure_openai: AzureOpenAIConfig
    dataset: str = Field(..., description="Path to JSONL scenarios file (relative to config file)")
    conversation: ConversationConfig = Field(default_factory=ConversationConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)


def load_eval_config(config_path: Path) -> EvalConfig:
    """Load evaluation config from a YAML file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        config_data = yaml.safe_load(f)

    config_data = _expand_env_vars(config_data)
    return EvalConfig(**config_data)
