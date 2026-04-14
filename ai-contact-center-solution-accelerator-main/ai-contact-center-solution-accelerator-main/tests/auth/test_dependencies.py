from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jwt import InvalidTokenError
from starlette.websockets import WebSocketDisconnect

from ai_contact_centre_solution_accelerator.auth.dependencies import authenticate_websocket


class TestAuthenticateWebsocket:
    @pytest.fixture
    def mock_websocket(self):
        ws = AsyncMock()
        ws.headers = {}
        ws.close = AsyncMock()
        return ws

    @pytest.fixture
    def mock_config_auth_disabled(self):
        config = MagicMock()
        config.authentication.enabled = False
        return config

    @pytest.fixture
    def mock_config_auth_enabled(self):
        config = MagicMock()
        config.authentication.enabled = True
        config.authentication.acs_resource_id = "test-resource"
        config.authentication.jwks_cache_lifespan = 300
        return config

    @pytest.mark.asyncio
    async def test_returns_none_when_auth_disabled(self, mock_websocket, mock_config_auth_disabled):
        with patch("ai_contact_centre_solution_accelerator.auth.dependencies.get_authenticator", return_value=None):
            result = await authenticate_websocket(mock_websocket, mock_config_auth_disabled)
            assert result is None
            mock_websocket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_closes_with_1008_when_no_auth_header(self, mock_websocket, mock_config_auth_enabled):
        mock_authenticator = MagicMock()

        with patch(
            "ai_contact_centre_solution_accelerator.auth.dependencies.get_authenticator",
            return_value=mock_authenticator,
        ):
            with pytest.raises(WebSocketDisconnect) as exc_info:
                await authenticate_websocket(mock_websocket, mock_config_auth_enabled)

            assert exc_info.value.code == 1008
            mock_websocket.close.assert_called_once_with(code=1008)

    @pytest.mark.asyncio
    async def test_closes_with_1008_when_invalid_bearer_format(self, mock_websocket, mock_config_auth_enabled):
        mock_websocket.headers = {"authorization": "Basic abc123"}
        mock_authenticator = MagicMock()

        with patch(
            "ai_contact_centre_solution_accelerator.auth.dependencies.get_authenticator",
            return_value=mock_authenticator,
        ):
            with pytest.raises(WebSocketDisconnect) as exc_info:
                await authenticate_websocket(mock_websocket, mock_config_auth_enabled)

            assert exc_info.value.code == 1008
            mock_websocket.close.assert_called_once_with(code=1008)

    @pytest.mark.asyncio
    async def test_closes_with_1008_when_token_invalid(self, mock_websocket, mock_config_auth_enabled):
        mock_websocket.headers = {"authorization": "Bearer invalid-token"}
        mock_authenticator = MagicMock()
        mock_authenticator.validate_token.side_effect = InvalidTokenError("Invalid")

        with patch(
            "ai_contact_centre_solution_accelerator.auth.dependencies.get_authenticator",
            return_value=mock_authenticator,
        ):
            with pytest.raises(WebSocketDisconnect) as exc_info:
                await authenticate_websocket(mock_websocket, mock_config_auth_enabled)

            assert exc_info.value.code == 1008
            mock_websocket.close.assert_called_once_with(code=1008)

    @pytest.mark.asyncio
    async def test_returns_claims_when_token_valid(self, mock_websocket, mock_config_auth_enabled):
        mock_websocket.headers = {"authorization": "Bearer valid-token"}
        mock_authenticator = MagicMock()
        mock_authenticator.validate_token.return_value = {"sub": "test-subject", "aud": "test-resource"}

        with patch(
            "ai_contact_centre_solution_accelerator.auth.dependencies.get_authenticator",
            return_value=mock_authenticator,
        ):
            result = await authenticate_websocket(mock_websocket, mock_config_auth_enabled)

            assert result == {"sub": "test-subject", "aud": "test-resource"}
            mock_websocket.close.assert_not_called()
            mock_authenticator.validate_token.assert_called_once_with("valid-token")
