"""Unit tests for ACS authentication."""

from unittest.mock import MagicMock, patch

import pytest
from jwt import InvalidTokenError

from ai_contact_centre_solution_accelerator.auth import acs_auth as acs_auth_module
from ai_contact_centre_solution_accelerator.auth.acs_auth import ISSUER, ACSAuthenticator, get_authenticator


@pytest.fixture(autouse=True)
def reset_authenticator():
    acs_auth_module._authenticator = None
    yield
    acs_auth_module._authenticator = None


class TestACSAuthenticator:
    def test_init_sets_audience_and_creates_jwks_client(self):
        with patch("ai_contact_centre_solution_accelerator.auth.acs_auth.PyJWKClient") as mock_client:
            auth = ACSAuthenticator(
                acs_resource_id="test-resource-id",
                jwks_cache_lifespan=600,
            )

            assert auth.audience == "test-resource-id"
            mock_client.assert_called_once()
            call_kwargs = mock_client.call_args
            assert call_kwargs[1]["lifespan"] == 600

    def test_validate_token_success(self):
        with patch("ai_contact_centre_solution_accelerator.auth.acs_auth.PyJWKClient") as mock_jwks_class:
            with patch("ai_contact_centre_solution_accelerator.auth.acs_auth.decode") as mock_decode:
                mock_jwks = MagicMock()
                mock_signing_key = MagicMock()
                mock_signing_key.key = "test-key"
                mock_jwks.get_signing_key_from_jwt.return_value = mock_signing_key
                mock_jwks_class.return_value = mock_jwks

                mock_decode.return_value = {"sub": "test-subject", "aud": "test-resource-id"}

                auth = ACSAuthenticator(acs_resource_id="test-resource-id")
                result = auth.validate_token("test-token")

                assert result["sub"] == "test-subject"
                mock_decode.assert_called_once_with(
                    "test-token",
                    "test-key",
                    algorithms=["RS256"],
                    issuer=ISSUER,
                    audience="test-resource-id",
                )

    def test_validate_token_invalid_raises_error(self):
        with patch("ai_contact_centre_solution_accelerator.auth.acs_auth.PyJWKClient") as mock_jwks_class:
            with patch("ai_contact_centre_solution_accelerator.auth.acs_auth.decode") as mock_decode:
                mock_jwks = MagicMock()
                mock_signing_key = MagicMock()
                mock_signing_key.key = "test-key"
                mock_jwks.get_signing_key_from_jwt.return_value = mock_signing_key
                mock_jwks_class.return_value = mock_jwks

                mock_decode.side_effect = InvalidTokenError("Invalid signature")

                auth = ACSAuthenticator(acs_resource_id="test-resource-id")

                with pytest.raises(InvalidTokenError, match="Invalid signature"):
                    auth.validate_token("bad-token")


class TestGetAuthenticator:
    def test_returns_none_when_auth_disabled(self):
        mock_config = MagicMock()
        mock_config.authentication.enabled = False

        result = get_authenticator(mock_config)
        assert result is None

    def test_returns_authenticator_when_enabled(self):
        mock_config = MagicMock()
        mock_config.authentication.enabled = True
        mock_config.authentication.acs_resource_id = "test-resource"
        mock_config.authentication.jwks_cache_lifespan = 300

        result = get_authenticator(mock_config)
        assert result is not None

    def test_returns_same_instance_on_multiple_calls(self):
        mock_config = MagicMock()
        mock_config.authentication.enabled = True
        mock_config.authentication.acs_resource_id = "test-resource"
        mock_config.authentication.jwks_cache_lifespan = 300

        result1 = get_authenticator(mock_config)
        result2 = get_authenticator(mock_config)
        assert result1 is result2
