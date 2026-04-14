from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from ai_contact_centre_solution_accelerator.config import ACSConfig, Config, get_config
from ai_contact_centre_solution_accelerator.routes import incoming
from ai_contact_centre_solution_accelerator.routes.incoming import (
    get_acs_client,
    incoming_call_router,
)


@pytest.fixture(autouse=True)
def reset_acs_client():
    incoming._acs_client = None
    yield
    incoming._acs_client = None


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.acs.connection_string = SecretStr("endpoint=https://test.communication.azure.com/;accesskey=test123")
    config.acs.callback_host = "test-app.azurecontainerapps.io"
    return config


@pytest.fixture
def mock_acs_client():
    client = MagicMock()
    answer_result = MagicMock()
    answer_result.call_connection_id = "test-connection-id"
    client.answer_call.return_value = answer_result
    return client


@pytest.fixture
def test_app(mock_config, mock_acs_client):
    app = FastAPI()
    app.include_router(incoming_call_router)
    app.dependency_overrides[get_acs_client] = lambda: mock_acs_client
    app.dependency_overrides[get_config] = lambda: mock_config

    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


class TestEventGridValidation:
    def test_returns_validation_response(self, client):
        events = [
            {
                "id": "test-id",
                "topic": "/subscriptions/test/resourceGroups/test/providers/Microsoft.Communication/CommunicationServices/test",
                "subject": "",
                "data": {"validationCode": "test-validation-code"},
                "eventType": "Microsoft.EventGrid.SubscriptionValidationEvent",
                "eventTime": "2024-01-01T00:00:00Z",
                "metadataVersion": "1",
                "dataVersion": "1",
            }
        ]

        response = client.post("/calls/incoming", json=events)

        assert response.status_code == 200
        assert response.json() == {"validationResponse": "test-validation-code"}


class TestIncomingCall:
    def test_answers_call_from_phone_number(self, client, mock_acs_client):
        events = [
            {
                "id": "test-id",
                "topic": "/subscriptions/test/resourceGroups/test/providers/Microsoft.Communication/CommunicationServices/test",
                "subject": "",
                "data": {
                    "from": {"kind": "phoneNumber", "phoneNumber": {"value": "+15551234567"}},
                    "to": {"kind": "phoneNumber", "phoneNumber": {"value": "+15559876543"}},
                    "incomingCallContext": "test-context",
                },
                "eventType": "Microsoft.Communication.IncomingCall",
                "eventTime": "2024-01-01T00:00:00Z",
                "metadataVersion": "1",
                "dataVersion": "1",
            }
        ]

        response = client.post("/calls/incoming", json=events)

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        mock_acs_client.answer_call.assert_called_once()

        call_kwargs = mock_acs_client.answer_call.call_args.kwargs
        assert call_kwargs["incoming_call_context"] == "test-context"
        assert "test-app.azurecontainerapps.io" in call_kwargs["callback_url"]
        assert "callerId=%2B15551234567" in call_kwargs["callback_url"]

    def test_answers_call_from_raw_id(self, client, mock_acs_client):
        events = [
            {
                "id": "test-id",
                "topic": "/subscriptions/test/resourceGroups/test/providers/Microsoft.Communication/CommunicationServices/test",
                "subject": "",
                "data": {
                    "from": {"kind": "communicationUser", "rawId": "8:acs:user-id"},
                    "to": {"kind": "phoneNumber", "phoneNumber": {"value": "+15559876543"}},
                    "incomingCallContext": "test-context",
                },
                "eventType": "Microsoft.Communication.IncomingCall",
                "eventTime": "2024-01-01T00:00:00Z",
                "metadataVersion": "1",
                "dataVersion": "1",
            }
        ]

        response = client.post("/calls/incoming", json=events)

        assert response.status_code == 200
        mock_acs_client.answer_call.assert_called_once()

        call_kwargs = mock_acs_client.answer_call.call_args.kwargs
        assert "callerId=8%3Aacs%3Auser-id" in call_kwargs["callback_url"]

    def test_configures_media_streaming(self, client, mock_acs_client):
        events = [
            {
                "id": "test-id",
                "topic": "/subscriptions/test/resourceGroups/test/providers/Microsoft.Communication/CommunicationServices/test",
                "subject": "",
                "data": {
                    "from": {"kind": "phoneNumber", "phoneNumber": {"value": "+15551234567"}},
                    "to": {"kind": "phoneNumber", "phoneNumber": {"value": "+15559876543"}},
                    "incomingCallContext": "test-context",
                },
                "eventType": "Microsoft.Communication.IncomingCall",
                "eventTime": "2024-01-01T00:00:00Z",
                "metadataVersion": "1",
                "dataVersion": "1",
            }
        ]

        response = client.post("/calls/incoming", json=events)

        assert response.status_code == 200
        call_kwargs = mock_acs_client.answer_call.call_args.kwargs
        media_streaming = call_kwargs["media_streaming"]

        assert media_streaming.transport_url == "wss://test-app.azurecontainerapps.io/ws?callerId=%2B15551234567"
        assert media_streaming.start_media_streaming is True
        assert media_streaming.enable_bidirectional is True

    def test_returns_ok_for_empty_events(self, client):
        response = client.post("/calls/incoming", json=[])

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_returns_ok_for_unhandled_event_type(self, client):
        events = [
            {
                "id": "test-id",
                "topic": "/subscriptions/test",
                "subject": "",
                "data": {},
                "eventType": "Microsoft.Communication.SomeOtherEvent",
                "eventTime": "2024-01-01T00:00:00Z",
                "metadataVersion": "1",
                "dataVersion": "1",
            }
        ]

        response = client.post("/calls/incoming", json=events)

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestCallEventsHandler:
    def test_handles_call_connected_event(self, client):
        events = [
            {
                "type": "Microsoft.Communication.CallConnected",
                "data": {
                    "callConnectionId": "test-connection-id",
                    "correlationId": "test-correlation-id",
                },
            }
        ]

        response = client.post("/calls/events/test-call-id", json=events)

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_handles_call_disconnected_event(self, client):
        events = [
            {
                "type": "Microsoft.Communication.CallDisconnected",
                "data": {
                    "callConnectionId": "test-connection-id",
                    "correlationId": "test-correlation-id",
                },
            }
        ]

        response = client.post("/calls/events/test-call-id", json=events)

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_handles_multiple_events(self, client):
        events = [
            {
                "type": "Microsoft.Communication.CallConnected",
                "data": {"callConnectionId": "conn-1", "correlationId": "corr-1"},
            },
            {
                "type": "Microsoft.Communication.CallDisconnected",
                "data": {"callConnectionId": "conn-1", "correlationId": "corr-1"},
            },
        ]

        response = client.post("/calls/events/test-call-id", json=events)

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestACSConfigValidation:
    def test_acs_config_requires_connection_string(self, monkeypatch):
        """Test that ACS_CONNECTION_STRING environment variable is required."""
        monkeypatch.delenv("ACS_CONNECTION_STRING", raising=False)
        monkeypatch.delenv("CONTAINER_APP_HOSTNAME", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            ACSConfig(_env_file=None)

        # Error message should mention connection_string is required
        error_msg = str(exc_info.value).lower()
        assert "connection_string" in error_msg or "field required" in error_msg

    def test_acs_config_callback_host_optional(self, monkeypatch):
        """Test that callback_host can be empty (will be auto-detected from CONTAINER_APP_HOSTNAME)."""
        monkeypatch.setenv("ACS_CONNECTION_STRING", "endpoint=https://test.com;accesskey=key")
        monkeypatch.delenv("CONTAINER_APP_HOSTNAME", raising=False)

        config = ACSConfig(_env_file=None)

        assert config.connection_string.get_secret_value() == "endpoint=https://test.com;accesskey=key"
        assert config.callback_host == ""

    def test_acs_config_valid(self, monkeypatch):
        """Test ACSConfig with valid configuration from environment variables."""
        monkeypatch.setenv("ACS_CONNECTION_STRING", "endpoint=https://test.com;accesskey=key")
        monkeypatch.setenv("CONTAINER_APP_HOSTNAME", "test-app.com")

        config = ACSConfig(_env_file=None)

        assert config.connection_string.get_secret_value() == "endpoint=https://test.com;accesskey=key"
        assert config.callback_host == "test-app.com"

    def test_config_acs_always_initialized(self):
        """Test that config.acs is always initialized with default_factory."""
        config = Config(
            azure_openai={"endpoint": "https://test.openai.azure.com/", "deployment": "gpt-4o"},
            agents=[{"name": "test", "description": "Test agent", "instructions": "Test"}],
        )

        assert config.acs is not None
        assert isinstance(config.acs, ACSConfig)
