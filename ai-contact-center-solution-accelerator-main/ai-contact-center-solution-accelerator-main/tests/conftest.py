"""
Pytest configuration and fixtures for AI Contact Centre tests.
"""

import os
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

os.environ.setdefault("ACS_CONNECTION_STRING", "endpoint=https://test.communication.azure.com/;accesskey=testkey123")

from ai_contact_centre_solution_accelerator.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def test_config_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for test configurations."""
    return tmp_path


@pytest.fixture
def minimal_config(test_config_dir: Path) -> Path:
    """Create a minimal valid configuration file."""
    config_data = {
        "app": {
            "name": "Test Contact Centre",
            "description": "Test description",
            "version": "1.0.0",
        },
        "azure_openai": {
            "endpoint": "https://test.openai.azure.com/",
            "deployment": "gpt-4o-realtime",
            "api_version": "2024-10-01-preview",
            "transcription_model": "gpt-4o-transcribe",
        },
        "server": {
            "host": "0.0.0.0",
            "port": 8000,
            "log_level": "INFO",
        },
        "voice": {
            "default": "alloy",
        },
        "turn_detection": {
            "type": "server_vad",
            "silence_duration_ms": 800,
            "threshold": 0.8,
            "create_response": True,
        },
        "agents": [
            {
                "name": "receptionist",
                "description": "A friendly receptionist",
                "voice": "alloy",
                "instructions": "You are a receptionist.",
                "plugins": [],
            }
        ],
        "handoffs": [],
        "plugins": [],
        "orchestration": {
            "silent_handoffs": True,
        },
    }

    config_path = test_config_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    return config_path


@pytest.fixture
def config_with_agents(test_config_dir: Path) -> Path:
    """Create a configuration file with agents defined."""
    config_data = {
        "app": {
            "name": "Test Contact Centre",
            "description": "Test description",
            "version": "1.0.0",
        },
        "azure_openai": {
            "endpoint": "https://test.openai.azure.com/",
            "deployment": "gpt-4o-realtime",
            "api_version": "2024-10-01-preview",
            "transcription_model": "gpt-4o-transcribe",
        },
        "server": {
            "host": "0.0.0.0",
            "port": 8000,
            "log_level": "INFO",
        },
        "voice": {
            "default": "alloy",
        },
        "turn_detection": {
            "type": "server_vad",
            "silence_duration_ms": 800,
            "threshold": 0.8,
            "create_response": True,
        },
        "agents": [
            {
                "name": "receptionist",
                "description": "A friendly receptionist",
                "voice": "alloy",
                "instructions": "You are a receptionist.",
                "plugins": [],
            },
            {
                "name": "billing",
                "description": "A billing specialist",
                "voice": "echo",
                "instructions": "You are a billing specialist.",
                "plugins": [],
            },
        ],
        "handoffs": [
            {
                "from": "receptionist",
                "to": "billing",
                "description": "Transfer for billing questions",
            },
            {
                "from": "billing",
                "to": "receptionist",
                "description": "Transfer for general questions",
            },
        ],
        "plugins": [],
        "orchestration": {
            "silent_handoffs": True,
        },
    }

    config_path = test_config_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    return config_path


@pytest.fixture
def config_with_plugins(test_config_dir: Path) -> Path:
    """Create a configuration file with plugins defined."""
    config_data = {
        "app": {
            "name": "Test Contact Centre",
            "description": "Test description",
            "version": "1.0.0",
        },
        "azure_openai": {
            "endpoint": "https://test.openai.azure.com/",
            "deployment": "gpt-4o-realtime",
            "api_version": "2024-10-01-preview",
            "transcription_model": "gpt-4o-transcribe",
        },
        "server": {
            "host": "0.0.0.0",
            "port": 8000,
            "log_level": "INFO",
        },
        "voice": {
            "default": "alloy",
        },
        "turn_detection": {
            "type": "server_vad",
            "silence_duration_ms": 800,
            "threshold": 0.8,
            "create_response": True,
        },
        "agents": [
            {
                "name": "receptionist",
                "description": "A friendly receptionist",
                "voice": "alloy",
                "instructions": "You are a receptionist.",
                "plugins": ["receptionist_plugin"],
            },
            {
                "name": "billing",
                "description": "A billing specialist",
                "voice": "echo",
                "instructions": "You are a billing specialist.",
                "plugins": [],
            },
        ],
        "handoffs": [],
        "plugins": [
            {
                "name": "receptionist_plugin",
                "module": "example_tools",
                "class_name": "ReceptionistPlugin",
                "description": "Receptionist plugin",
            },
        ],
        "orchestration": {
            "silent_handoffs": True,
        },
    }

    config_path = test_config_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    return config_path


@pytest.fixture(autouse=True)
def reset_config():
    """Reset the global config instance before each test."""
    from ai_contact_centre_solution_accelerator import config as config_module

    config_module._config = None
    yield
    config_module._config = None
