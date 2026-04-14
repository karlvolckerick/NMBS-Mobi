from pathlib import Path

import pytest
import yaml
from pydantic import SecretStr

from ai_contact_centre_solution_accelerator.config import (
    ACSConfig,
    AgentConfig,
    AuthenticationConfig,
    AzureOpenAIConfig,
    MCPServerConfig,
    NoiseReductionConfig,
    SemanticVadConfig,
    VoiceLiveConfig,
    _expand_env_vars,
    load_config,
)


class TestConfigLoading:
    def test_load_minimal_config(self, minimal_config: Path):
        config = load_config(minimal_config)

        assert config.app.name == "Test Contact Centre"
        assert config.azure_openai.endpoint == "https://test.openai.azure.com/"
        assert config.server.port == 8000
        assert config.voice.default == "alloy"
        assert len(config.agents) == 1

    def test_config_has_voicelive_field(self, minimal_config: Path):
        config = load_config(minimal_config)

        assert hasattr(config, "voicelive")
        assert config.voicelive.noise_reduction.enabled is True

    def test_load_config_with_agents(self, config_with_agents: Path):
        config = load_config(config_with_agents)

        assert len(config.agents) == 2
        assert config.agents[0].name == "receptionist"
        assert config.agents[1].name == "billing"

    def test_load_config_with_handoffs(self, config_with_agents: Path):
        config = load_config(config_with_agents)

        assert len(config.handoffs) == 2
        assert config.handoffs[0].from_agent == "receptionist"
        assert config.handoffs[0].to == "billing"

    def test_config_not_found(self, test_config_dir: Path):
        with pytest.raises(FileNotFoundError):
            load_config(test_config_dir / "nonexistent.yaml")


class TestAzureOpenAIConfig:
    def test_client_type_defaults_to_voicelive(self):
        config = AzureOpenAIConfig(endpoint="https://test.openai.azure.com/")
        assert config.client_type == "voicelive"

    def test_client_type_can_be_realtime(self):
        config = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            client_type="realtime",
        )
        assert config.client_type == "realtime"

    def test_client_type_invalid_value_raises(self):
        with pytest.raises(ValueError):
            AzureOpenAIConfig(
                endpoint="https://test.openai.azure.com/",
                client_type="invalid",
            )


class TestVoiceLiveConfig:
    def test_voicelive_config_defaults(self):
        config = VoiceLiveConfig()

        assert config.noise_reduction.enabled is True
        assert config.echo_cancellation.enabled is True
        assert config.semantic_vad.enabled is False
        assert config.semantic_vad.eagerness == "medium"
        assert config.semantic_vad.remove_filler_words is True
        assert config.semantic_vad.end_of_utterance.threshold == 0.5
        assert config.semantic_vad.end_of_utterance.timeout == 500
        assert config.voice.type == "azure-standard"
        assert config.voice.rate == "1.0"
        assert config.voice.temperature == 0.8
        assert config.voice.endpoint_id == ""
        assert config.voice.custom_lexicon_url == ""
        assert config.animation.viseme_enabled is False

    def test_voicelive_config_custom_values(self):
        config = VoiceLiveConfig(
            noise_reduction=NoiseReductionConfig(enabled=False),
            semantic_vad=SemanticVadConfig(enabled=True, eagerness="high"),
        )

        assert config.noise_reduction.enabled is False
        assert config.semantic_vad.enabled is True
        assert config.semantic_vad.eagerness == "high"


class TestAgentConfig:
    def test_valid_agent_name(self):
        agent = AgentConfig(
            name="receptionist",
            description="A receptionist",
            instructions="Be helpful",
        )
        assert agent.name == "receptionist"

    def test_agent_name_with_underscore(self):
        agent = AgentConfig(
            name="billing_specialist",
            description="A billing specialist",
            instructions="Handle billing",
        )
        assert agent.name == "billing_specialist"

    def test_invalid_agent_name_uppercase(self):
        with pytest.raises(ValueError):
            AgentConfig(
                name="Receptionist",
                description="A receptionist",
                instructions="Be helpful",
            )

    def test_invalid_agent_name_starts_with_number(self):
        with pytest.raises(ValueError):
            AgentConfig(
                name="1receptionist",
                description="A receptionist",
                instructions="Be helpful",
            )

    def test_valid_voice(self):
        agent = AgentConfig(
            name="test",
            description="Test",
            instructions="Test",
            voice="shimmer",
        )
        assert agent.voice == "shimmer"

    def test_azure_tts_voice(self):
        agent = AgentConfig(
            name="test",
            description="Test",
            instructions="Test",
            voice="en-US-AvaMultilingualNeural",
        )
        assert agent.voice == "en-US-AvaMultilingualNeural"

    def test_voice_defaults_to_none(self):
        agent = AgentConfig(
            name="test",
            description="Test",
            instructions="Test",
        )
        assert agent.voice is None


class TestConfigValidation:
    def test_validate_handoffs_missing_source(self, test_config_dir: Path):
        config_data = {
            "app": {"name": "Test", "description": "Test", "version": "1.0.0"},
            "azure_openai": {"endpoint": "https://test.openai.azure.com/", "deployment": "gpt-4o-realtime"},
            "server": {"host": "0.0.0.0", "port": 8000, "log_level": "INFO"},
            "voice": {"default": "alloy"},
            "turn_detection": {
                "type": "server_vad",
                "silence_duration_ms": 800,
                "threshold": 0.8,
                "create_response": True,
            },
            "agents": [
                {"name": "billing", "description": "Billing", "instructions": "Handle billing"},
            ],
            "handoffs": [
                {"from": "nonexistent", "to": "billing", "description": "Transfer"},
            ],
            "plugins": [],
            "orchestration": {"silent_handoffs": True},
        }

        config_path = test_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError, match="does not exist"):
            load_config(config_path)

    def test_validate_handoffs_missing_target(self, test_config_dir: Path):
        config_data = {
            "app": {"name": "Test", "description": "Test", "version": "1.0.0"},
            "azure_openai": {"endpoint": "https://test.openai.azure.com/", "deployment": "gpt-4o-realtime"},
            "server": {"host": "0.0.0.0", "port": 8000, "log_level": "INFO"},
            "voice": {"default": "alloy"},
            "turn_detection": {
                "type": "server_vad",
                "silence_duration_ms": 800,
                "threshold": 0.8,
                "create_response": True,
            },
            "agents": [
                {"name": "receptionist", "description": "Receptionist", "instructions": "Be helpful"},
            ],
            "handoffs": [
                {"from": "receptionist", "to": "nonexistent", "description": "Transfer"},
            ],
            "plugins": [],
            "orchestration": {"silent_handoffs": True},
        }

        config_path = test_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError, match="does not exist"):
            load_config(config_path)

    def test_validate_handoffs_self_reference(self, test_config_dir: Path):
        config_data = {
            "app": {"name": "Test", "description": "Test", "version": "1.0.0"},
            "azure_openai": {"endpoint": "https://test.openai.azure.com/", "deployment": "gpt-4o-realtime"},
            "server": {"host": "0.0.0.0", "port": 8000, "log_level": "INFO"},
            "voice": {"default": "alloy"},
            "turn_detection": {
                "type": "server_vad",
                "silence_duration_ms": 800,
                "threshold": 0.8,
                "create_response": True,
            },
            "agents": [
                {"name": "receptionist", "description": "Receptionist", "instructions": "Be helpful"},
            ],
            "handoffs": [
                {"from": "receptionist", "to": "receptionist", "description": "Self transfer"},
            ],
            "plugins": [],
            "orchestration": {"silent_handoffs": True},
        }

        config_path = test_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError, match="cannot hand off to itself"):
            load_config(config_path)

    def test_validate_plugins_missing(self, test_config_dir: Path):
        config_data = {
            "app": {"name": "Test", "description": "Test", "version": "1.0.0"},
            "azure_openai": {"endpoint": "https://test.openai.azure.com/", "deployment": "gpt-4o-realtime"},
            "server": {"host": "0.0.0.0", "port": 8000, "log_level": "INFO"},
            "voice": {"default": "alloy"},
            "turn_detection": {
                "type": "server_vad",
                "silence_duration_ms": 800,
                "threshold": 0.8,
                "create_response": True,
            },
            "agents": [
                {
                    "name": "receptionist",
                    "description": "Receptionist",
                    "instructions": "Be helpful",
                    "plugins": ["nonexistent_plugin"],
                },
            ],
            "handoffs": [],
            "plugins": [],
            "orchestration": {"silent_handoffs": True},
        }

        config_path = test_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError, match="unknown plugin"):
            load_config(config_path)


class TestConfigHelpers:
    def test_get_agent_by_name(self, config_with_agents: Path):
        config = load_config(config_with_agents)

        agent = config.get_agent_by_name("receptionist")
        assert agent is not None
        assert agent.name == "receptionist"

        agent = config.get_agent_by_name("nonexistent")
        assert agent is None

    def test_get_plugins_for_agent(self, config_with_plugins: Path):
        config = load_config(config_with_plugins)

        plugins = config.get_plugins_for_agent("receptionist")
        assert len(plugins) == 1
        assert plugins[0].name == "receptionist_plugin"

        plugins = config.get_plugins_for_agent("billing")
        assert len(plugins) == 0


class TestAuthenticationConfig:
    def test_authentication_config_defaults(self):
        auth_config = AuthenticationConfig()
        assert auth_config.enabled is False
        assert auth_config.acs_resource_id == ""
        assert auth_config.jwks_cache_lifespan == 300

    def test_authentication_config_from_values(self):
        auth_config = AuthenticationConfig(
            enabled=True,
            acs_resource_id="/subscriptions/test/resourceGroups/rg/providers/Microsoft.Communication/CommunicationServices/acs",
            jwks_cache_lifespan=600,
        )
        assert auth_config.enabled is True
        assert "test" in auth_config.acs_resource_id
        assert auth_config.jwks_cache_lifespan == 600

    def test_authentication_config_env_override(self, monkeypatch):
        monkeypatch.setenv("ACS_AUTH_ENABLED", "true")
        monkeypatch.setenv("ACS_AUTH_ACS_RESOURCE_ID", "env-resource-id")

        auth_config = AuthenticationConfig()
        assert auth_config.enabled is True
        assert auth_config.acs_resource_id == "env-resource-id"

    def test_validate_authentication_enabled_without_resource_id(self, test_config_dir: Path):
        config_data = {
            "app": {"name": "Test", "description": "Test", "version": "1.0.0"},
            "azure_openai": {"endpoint": "https://test.openai.azure.com/", "deployment": "gpt-4o-realtime"},
            "server": {"host": "0.0.0.0", "port": 8000, "log_level": "INFO"},
            "voice": {"default": "alloy"},
            "turn_detection": {
                "type": "server_vad",
                "silence_duration_ms": 800,
                "threshold": 0.8,
                "create_response": True,
            },
            "agents": [{"name": "receptionist", "description": "Receptionist", "instructions": "Be helpful"}],
            "handoffs": [],
            "plugins": [],
            "orchestration": {"silent_handoffs": True},
            "authentication": {"enabled": True, "acs_resource_id": ""},
        }

        config_path = test_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError, match="acs_resource_id is required"):
            load_config(config_path)

    def test_validate_authentication_disabled_without_resource_id(self, test_config_dir: Path):
        config_data = {
            "app": {"name": "Test", "description": "Test", "version": "1.0.0"},
            "azure_openai": {"endpoint": "https://test.openai.azure.com/", "deployment": "gpt-4o-realtime"},
            "server": {"host": "0.0.0.0", "port": 8000, "log_level": "INFO"},
            "voice": {"default": "alloy"},
            "turn_detection": {
                "type": "server_vad",
                "silence_duration_ms": 800,
                "threshold": 0.8,
                "create_response": True,
            },
            "agents": [{"name": "receptionist", "description": "Receptionist", "instructions": "Be helpful"}],
            "handoffs": [],
            "plugins": [],
            "orchestration": {"silent_handoffs": True},
            "authentication": {"enabled": False, "acs_resource_id": ""},
        }

        config_path = test_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(config_path)
        assert config.authentication.enabled is False


class TestACSConfig:
    def test_acs_config_defaults(self, monkeypatch):
        """Test ACSConfig with default values when only connection_string is provided."""
        monkeypatch.delenv("CONTAINER_APP_HOSTNAME", raising=False)
        monkeypatch.delenv("ACS_CALLBACK_HOST", raising=False)
        monkeypatch.setenv("ACS_CONNECTION_STRING", "test-connection-string")

        acs_config = ACSConfig(_env_file=None)
        assert acs_config.connection_string.get_secret_value() == "test-connection-string"
        assert acs_config.callback_host == ""

    def test_acs_config_with_container_app_hostname(self, monkeypatch):
        """Test ACSConfig with explicit CONTAINER_APP_HOSTNAME environment variable."""
        monkeypatch.setenv("ACS_CONNECTION_STRING", "test-connection-string")
        monkeypatch.setenv("CONTAINER_APP_HOSTNAME", "example.azurecontainerapps.io")

        acs_config = ACSConfig(_env_file=None)
        assert acs_config.connection_string.get_secret_value() == "test-connection-string"
        assert acs_config.callback_host == "example.azurecontainerapps.io"

    def test_acs_config_requires_connection_string(self, monkeypatch):
        """Test that ACSConfig requires ACS_CONNECTION_STRING to be set."""
        monkeypatch.delenv("ACS_CONNECTION_STRING", raising=False)
        monkeypatch.delenv("CONTAINER_APP_HOSTNAME", raising=False)

        with pytest.raises(Exception):  # ValidationError from pydantic
            ACSConfig(_env_file=None)

    def test_config_acs_field_always_initialized(self, minimal_config: Path):
        """Test that config.acs is always initialized with default_factory."""
        config = load_config(minimal_config)
        assert config.acs is not None
        assert isinstance(config.acs, ACSConfig)


class TestExpandEnvVars:
    def test_expand_string(self, monkeypatch):
        monkeypatch.setenv("MY_SECRET", "abc123")
        assert _expand_env_vars("Bearer ${MY_SECRET}") == "Bearer abc123"

    def test_expand_nested_dict(self, monkeypatch):
        monkeypatch.setenv("HOST", "example.com")
        data = {"url": "https://${HOST}/api", "port": 8080}
        result = _expand_env_vars(data)
        assert result == {"url": "https://example.com/api", "port": 8080}

    def test_expand_list(self, monkeypatch):
        monkeypatch.setenv("ARG", "hello")
        data = ["${ARG}", "world"]
        result = _expand_env_vars(data)
        assert result == ["hello", "world"]

    def test_missing_env_var_left_as_is(self):
        assert _expand_env_vars("${DOES_NOT_EXIST_XYZ}") == "${DOES_NOT_EXIST_XYZ}"

    def test_non_string_passthrough(self):
        assert _expand_env_vars(42) == 42
        assert _expand_env_vars(True) is True
        assert _expand_env_vars(None) is None


class TestMCPServerConfig:
    def test_http_server_config(self):
        config = MCPServerConfig(
            name="crm",
            transport="http",
            url="https://crm.example.com/mcp",
            headers={"Authorization": SecretStr("Bearer secret")},
        )
        assert config.name == "crm"
        assert config.transport == "http"
        assert config.url == "https://crm.example.com/mcp"
        assert config.headers["Authorization"].get_secret_value() == "Bearer secret"
        assert config.enabled is True

    def test_stdio_server_config(self):
        config = MCPServerConfig(
            name="kb",
            transport="stdio",
            command="npx",
            args=["-y", "@company/kb-server"],
            env={"API_KEY": SecretStr("secret")},
        )
        assert config.name == "kb"
        assert config.transport == "stdio"
        assert config.command == "npx"
        assert config.args == ["-y", "@company/kb-server"]
        assert config.env["API_KEY"].get_secret_value() == "secret"

    def test_disabled_server(self):
        config = MCPServerConfig(
            name="test",
            transport="http",
            url="https://example.com",
            enabled=False,
        )
        assert config.enabled is False

    def test_invalid_transport_raises(self):
        with pytest.raises(ValueError):
            MCPServerConfig(name="test", transport="grpc")

    def test_agent_config_mcp_servers_default_empty(self):
        agent = AgentConfig(
            name="test",
            description="Test",
            instructions="Test",
        )
        assert agent.mcp_servers == []

    def test_agent_config_with_mcp_servers(self):
        agent = AgentConfig(
            name="test",
            description="Test",
            instructions="Test",
            mcp_servers=["crm", "kb"],
        )
        assert agent.mcp_servers == ["crm", "kb"]


class TestMCPServerValidation:
    def test_validate_mcp_unknown_server_reference(self, test_config_dir: Path):
        config_data = {
            "app": {"name": "Test", "description": "Test", "version": "1.0.0"},
            "azure_openai": {"endpoint": "https://test.openai.azure.com/", "deployment": "gpt-4o-realtime"},
            "server": {"host": "0.0.0.0", "port": 8000, "log_level": "INFO"},
            "voice": {"default": "alloy"},
            "turn_detection": {
                "type": "server_vad",
                "silence_duration_ms": 800,
                "threshold": 0.8,
                "create_response": True,
            },
            "agents": [
                {
                    "name": "receptionist",
                    "description": "Receptionist",
                    "instructions": "Be helpful",
                    "mcp_servers": ["nonexistent"],
                },
            ],
            "handoffs": [],
            "plugins": [],
            "mcp_servers": [],
            "orchestration": {"silent_handoffs": True},
        }

        config_path = test_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError, match="unknown MCP server"):
            load_config(config_path)

    def test_validate_mcp_http_missing_url(self, test_config_dir: Path):
        config_data = {
            "app": {"name": "Test", "description": "Test", "version": "1.0.0"},
            "azure_openai": {"endpoint": "https://test.openai.azure.com/", "deployment": "gpt-4o-realtime"},
            "server": {"host": "0.0.0.0", "port": 8000, "log_level": "INFO"},
            "voice": {"default": "alloy"},
            "turn_detection": {
                "type": "server_vad",
                "silence_duration_ms": 800,
                "threshold": 0.8,
                "create_response": True,
            },
            "agents": [
                {"name": "receptionist", "description": "Receptionist", "instructions": "Be helpful"},
            ],
            "handoffs": [],
            "plugins": [],
            "mcp_servers": [{"name": "bad", "transport": "http"}],
            "orchestration": {"silent_handoffs": True},
        }

        config_path = test_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError, match="requires 'url'"):
            load_config(config_path)

    def test_validate_mcp_stdio_missing_command(self, test_config_dir: Path):
        config_data = {
            "app": {"name": "Test", "description": "Test", "version": "1.0.0"},
            "azure_openai": {"endpoint": "https://test.openai.azure.com/", "deployment": "gpt-4o-realtime"},
            "server": {"host": "0.0.0.0", "port": 8000, "log_level": "INFO"},
            "voice": {"default": "alloy"},
            "turn_detection": {
                "type": "server_vad",
                "silence_duration_ms": 800,
                "threshold": 0.8,
                "create_response": True,
            },
            "agents": [
                {"name": "receptionist", "description": "Receptionist", "instructions": "Be helpful"},
            ],
            "handoffs": [],
            "plugins": [],
            "mcp_servers": [{"name": "bad", "transport": "stdio"}],
            "orchestration": {"silent_handoffs": True},
        }

        config_path = test_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError, match="requires 'command'"):
            load_config(config_path)

    def test_validate_mcp_disabled_server_skipped(self, test_config_dir: Path):
        config_data = {
            "app": {"name": "Test", "description": "Test", "version": "1.0.0"},
            "azure_openai": {"endpoint": "https://test.openai.azure.com/", "deployment": "gpt-4o-realtime"},
            "server": {"host": "0.0.0.0", "port": 8000, "log_level": "INFO"},
            "voice": {"default": "alloy"},
            "turn_detection": {
                "type": "server_vad",
                "silence_duration_ms": 800,
                "threshold": 0.8,
                "create_response": True,
            },
            "agents": [
                {"name": "receptionist", "description": "Receptionist", "instructions": "Be helpful"},
            ],
            "handoffs": [],
            "plugins": [],
            "mcp_servers": [{"name": "disabled", "transport": "http", "enabled": False}],
            "orchestration": {"silent_handoffs": True},
        }

        config_path = test_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(config_path)
        assert len(config.mcp_servers) == 1
        assert config.mcp_servers[0].enabled is False
