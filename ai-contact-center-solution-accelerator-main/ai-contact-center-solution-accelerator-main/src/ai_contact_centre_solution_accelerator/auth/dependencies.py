"""FastAPI dependencies for authentication."""

import logging
from typing import Annotated

from fastapi import Depends, WebSocket
from jwt import InvalidTokenError
from starlette.websockets import WebSocketDisconnect

from ai_contact_centre_solution_accelerator.auth.acs_auth import get_authenticator
from ai_contact_centre_solution_accelerator.config import Config, get_config

logger = logging.getLogger(__name__)


async def authenticate_websocket(
    websocket: WebSocket,
    config: Annotated[Config, Depends(get_config)],
) -> dict | None:
    """Dependency that validates ACS JWT token.

    Args:
        websocket: The WebSocket connection.
        config: Application configuration.

    Returns:
        Decoded token claims if auth enabled and valid, None if auth disabled.

    Raises:
        WebSocketDisconnect: If auth enabled and token invalid/missing.
    """
    authenticator = get_authenticator(config)
    if authenticator is None:
        return None

    auth_header = websocket.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        logger.warning("WebSocket connection missing Bearer token")
        await websocket.close(code=1008)
        raise WebSocketDisconnect(code=1008)

    token = auth_header.split(" ", 1)[1]
    try:
        decoded = authenticator.validate_token(token)
        logger.info(f"Authenticated WebSocket connection: {decoded.get('sub', 'unknown')}")
        return decoded
    except InvalidTokenError as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008)
        raise WebSocketDisconnect(code=1008)
