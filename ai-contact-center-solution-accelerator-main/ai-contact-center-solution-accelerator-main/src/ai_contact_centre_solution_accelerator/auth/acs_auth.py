from jwt import PyJWKClient, decode

from ai_contact_centre_solution_accelerator.config import Config

JWKS_URL = "https://acscallautomation.communication.azure.com/calling/keys"
ISSUER = "https://acscallautomation.communication.azure.com"


class ACSAuthenticator:
    """Validates JWT tokens from Azure Communication Services."""

    def __init__(self, acs_resource_id: str, jwks_cache_lifespan: int = 300):
        """Initialize authenticator.

        Args:
            acs_resource_id: ACS resource ID used as JWT audience.
            jwks_cache_lifespan: Seconds to cache JWKS keys.
        """
        self.audience = acs_resource_id
        self.jwks_client = PyJWKClient(JWKS_URL, lifespan=jwks_cache_lifespan)

    def validate_token(self, token: str) -> dict:
        """Validate JWT and return decoded payload.

        Args:
            token: JWT token string.

        Returns:
            Decoded token claims.

        Raises:
            InvalidTokenError: If token validation fails.
        """
        signing_key = self.jwks_client.get_signing_key_from_jwt(token)
        return decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=self.audience,
        )


_authenticator: ACSAuthenticator | None = None


def get_authenticator(config: Config) -> ACSAuthenticator | None:
    """Get or create singleton authenticator.

    Args:
        config: Application configuration.

    Returns:
        ACSAuthenticator instance if auth enabled, None otherwise.
    """
    global _authenticator
    if not config.authentication.enabled:
        return None
    if _authenticator is None:
        _authenticator = ACSAuthenticator(
            acs_resource_id=config.authentication.acs_resource_id,
            jwks_cache_lifespan=config.authentication.jwks_cache_lifespan,
        )
    return _authenticator
