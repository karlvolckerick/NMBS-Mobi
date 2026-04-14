import os
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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


class AppConfig(BaseModel):
    name: str = "AI Contact Centre Solution Accelerator"
    description: str = "Multi-agent realtime voice assistant with intelligent handoffs"
    version: str = "1.0.0"


class AzureOpenAIConfig(BaseModel):
    endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    deployment: str = Field(default="gpt-4o-realtime", description="Deployment name")
    api_version: str = Field(default="2024-10-01-preview", description="API version")
    transcription_model: str = Field(default="gpt-4o-transcribe", description="Transcription model")
    client_type: Literal["realtime", "voicelive"] = Field(
        default="voicelive", description="Client type: realtime or voicelive"
    )


class NoiseReductionConfig(BaseModel):
    enabled: bool = Field(default=True)


class EchoCancellationConfig(BaseModel):
    enabled: bool = Field(default=True)


class EndOfUtteranceConfig(BaseModel):
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    timeout: int = Field(default=500, ge=0)


class SemanticVadConfig(BaseModel):
    enabled: bool = Field(default=False)
    eagerness: Literal["low", "medium", "high", "auto"] = Field(default="medium")
    interrupt_response: bool = Field(default=True, description="Whether to interrupt agent speech on new user input")
    remove_filler_words: bool = Field(default=True)
    end_of_utterance: EndOfUtteranceConfig = Field(default_factory=EndOfUtteranceConfig)


class VoiceLiveVoiceConfig(BaseModel):
    type: Literal["azure-standard", "azure-custom"] = Field(default="azure-standard")
    rate: str = Field(default="1.0")
    temperature: float = Field(default=0.8, ge=0.0, le=1.0)
    endpoint_id: str = Field(default="")
    custom_lexicon_url: str = Field(default="")


class AnimationConfig(BaseModel):
    viseme_enabled: bool = Field(default=False)


class VoiceLiveConfig(BaseModel):
    noise_reduction: NoiseReductionConfig = Field(default_factory=NoiseReductionConfig)
    echo_cancellation: EchoCancellationConfig = Field(default_factory=EchoCancellationConfig)
    semantic_vad: SemanticVadConfig = Field(default_factory=SemanticVadConfig)
    voice: VoiceLiveVoiceConfig = Field(default_factory=VoiceLiveVoiceConfig)
    animation: AnimationConfig = Field(default_factory=AnimationConfig)


class ServerConfig(BaseModel):
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    log_level: str = Field(default="INFO", description="Logging level")


class VoiceConfig(BaseModel):
    default: str = Field(default="alloy", description="Default voice")


class TurnDetectionConfig(BaseModel):
    type: str = Field(default="server_vad", description="Turn detection type")
    silence_duration_ms: int = Field(default=800, description="Silence duration in ms")
    threshold: float = Field(default=0.8, description="Detection threshold")
    create_response: bool = Field(default=True, description="Auto-create response")


class AgentConfig(BaseModel):
    name: str = Field(..., description="Unique agent identifier")
    description: str = Field(..., description="Agent description for handoffs")
    voice: str | None = Field(default=None, description="Voice for this agent (Azure TTS name or OpenAI voice)")
    instructions: str = Field(..., description="System instructions for the agent")
    plugins: list[str] = Field(default_factory=list, description="List of plugin names to assign")
    mcp_servers: list[str] = Field(default_factory=list, description="List of MCP server names to assign")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError(
                "Agent name must start with lowercase letter and contain only lowercase letters, numbers, and underscores"
            )
        return v


class HandoffConfig(BaseModel):
    from_agent: str = Field(..., alias="from", description="Source agent name")
    to: str = Field(..., description="Target agent name")
    description: str = Field(..., description="Handoff description/trigger")


class PluginConfig(BaseModel):
    name: str = Field(..., description="Plugin name (referenced by agents)")
    module: str = Field(..., description="Python module name in src/tools/")
    class_name: str = Field(..., description="Class name within the module")
    description: str = Field(default="", description="Plugin description")


class MCPServerConfig(BaseModel):
    """Configuration for an MCP (Model Context Protocol) server."""

    name: str = Field(..., description="MCP server name (referenced by agents)")
    transport: Literal["http", "stdio"] = Field(..., description="Transport type")
    description: str = Field(default="", description="Server description")
    enabled: bool = Field(default=True, description="Whether this server is enabled")

    url: str | None = Field(default=None, description="Server URL (http transport)")
    headers: dict[str, SecretStr] | None = Field(default=None, description="HTTP headers")

    command: str | None = Field(default=None, description="Command to run (stdio transport)")
    args: list[str] | None = Field(default=None, description="Command arguments")
    env: dict[str, SecretStr] | None = Field(default=None, description="Environment variables")


class OrchestrationConfig(BaseModel):
    silent_handoffs: bool = Field(default=True, description="Enable silent handoffs")


class ACSConfig(BaseSettings):
    """Azure Communication Services configuration."""

    model_config = SettingsConfigDict(env_prefix="ACS_")

    connection_string: SecretStr = Field(description="ACS connection string")
    callback_host: str = Field(
        default="",
        alias="CONTAINER_APP_HOSTNAME",
        description="Callback host URI for ACS events. If not set, uses CONTAINER_APP_HOSTNAME in Azure Container Apps.",
    )


class AuthenticationConfig(BaseSettings):
    """Authentication configuration with environment variable support."""

    model_config = SettingsConfigDict(env_prefix="ACS_AUTH_")

    enabled: bool = Field(default=False, description="Enable ACS JWT authentication")
    acs_resource_id: str = Field(default="", description="ACS resource ID (audience claim)")
    jwks_cache_lifespan: int = Field(default=300, description="JWKS cache TTL in seconds")


class Config(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    azure_openai: AzureOpenAIConfig
    voicelive: VoiceLiveConfig = Field(default_factory=VoiceLiveConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    turn_detection: TurnDetectionConfig = Field(default_factory=TurnDetectionConfig)
    agents: list[AgentConfig] = Field(default_factory=list, min_length=1)
    handoffs: list[HandoffConfig] = Field(default_factory=list)
    plugins: list[PluginConfig] = Field(default_factory=list)
    mcp_servers: list[MCPServerConfig] = Field(default_factory=list)
    orchestration: OrchestrationConfig = Field(default_factory=OrchestrationConfig)
    acs: ACSConfig = Field(default_factory=ACSConfig)
    authentication: AuthenticationConfig = Field(default_factory=AuthenticationConfig)

    def get_agent_by_name(self, name: str) -> AgentConfig | None:
        """Get an agent configuration by name."""
        for agent in self.agents:
            if agent.name == name:
                return agent
        return None

    def get_plugins_for_agent(self, agent_name: str) -> list[PluginConfig]:
        """Get all plugins assigned to an agent."""
        agent = self.get_agent_by_name(agent_name)
        if not agent:
            return []
        return [p for p in self.plugins if p.name in agent.plugins]

    def validate_handoffs(self) -> list[str]:
        errors = []
        agent_names = {agent.name for agent in self.agents}

        for handoff in self.handoffs:
            if handoff.from_agent not in agent_names:
                errors.append(f"Handoff source agent '{handoff.from_agent}' does not exist")
            if handoff.to not in agent_names:
                errors.append(f"Handoff target agent '{handoff.to}' does not exist")
            if handoff.from_agent == handoff.to:
                errors.append(f"Agent '{handoff.from_agent}' cannot hand off to itself")

        return errors

    def validate_plugins(self) -> list[str]:
        errors = []
        plugin_names = {plugin.name for plugin in self.plugins}

        for agent in self.agents:
            for plugin_name in agent.plugins:
                if plugin_name not in plugin_names:
                    errors.append(f"Agent '{agent.name}' references unknown plugin '{plugin_name}'")

        return errors

    def validate_authentication(self) -> list[str]:
        """Validate authentication configuration."""
        errors = []
        if self.authentication.enabled and not self.authentication.acs_resource_id:
            errors.append("authentication.acs_resource_id is required when authentication is enabled")
        return errors

    def validate_mcp_servers(self) -> list[str]:
        """Validate MCP server configuration."""
        errors = []
        server_names = {s.name for s in self.mcp_servers}

        for agent in self.agents:
            for server_name in agent.mcp_servers:
                if server_name not in server_names:
                    errors.append(f"Agent '{agent.name}' references unknown MCP server '{server_name}'")

        for server in self.mcp_servers:
            if not server.enabled:
                continue
            if server.transport == "http" and not server.url:
                errors.append(f"MCP server '{server.name}' (http) requires 'url'")
            if server.transport == "stdio" and not server.command:
                errors.append(f"MCP server '{server.name}' (stdio) requires 'command'")

        return errors


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config.yaml. Defaults to config.yaml in project root.

    Returns:
        Validated Config object.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValidationError: If config validation fails.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config.yaml"

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path) as f:
        config_data = yaml.safe_load(f)

    config_data = _expand_env_vars(config_data)
    config = Config(**config_data)

    handoff_errors = config.validate_handoffs()
    plugin_errors = config.validate_plugins()
    auth_errors = config.validate_authentication()
    mcp_errors = config.validate_mcp_servers()

    all_errors = handoff_errors + plugin_errors + auth_errors + mcp_errors
    if all_errors:
        raise ValueError("Configuration validation errors:\n" + "\n".join(f"  - {e}" for e in all_errors))

    return config


_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = load_config()
    return _config
