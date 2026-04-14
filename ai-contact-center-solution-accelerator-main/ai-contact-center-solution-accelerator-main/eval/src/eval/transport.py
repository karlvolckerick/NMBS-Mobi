import base64
import json
import logging
from typing import Any, AsyncIterator

import websockets

logger = logging.getLogger(__name__)


class WebSocketTransport:
    """WebSocket client for communicating with the accelerator's /ws endpoint."""

    def __init__(self, url: str, headers: dict[str, str] | None = None) -> None:
        self.url = url
        self.headers = headers or {}
        self._ws: websockets.ClientConnection | None = None

    async def __aenter__(self) -> "WebSocketTransport":
        self._ws = await websockets.connect(self.url, additional_headers=self.headers)
        logger.info("Connected to %s", self.url)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._ws is not None:
            await self._ws.close()
            logger.info("Disconnected from %s", self.url)
            self._ws = None

    @property
    def is_connected(self) -> bool:
        return self._ws is not None

    async def send_audio(self, pcm_data: bytes) -> None:
        """Send PCM audio as a base64-encoded AudioData message."""
        if self._ws is None:
            raise RuntimeError("WebSocket is not connected")

        message = {
            "kind": "AudioData",
            "audioData": {"data": base64.b64encode(pcm_data).decode("utf-8")},
        }
        await self._ws.send(json.dumps(message))

    async def receive(self) -> AsyncIterator[dict[str, Any]]:
        """Yield parsed JSON events from the WebSocket."""
        if self._ws is None:
            raise RuntimeError("WebSocket is not connected")

        async for message in self._ws:
            yield json.loads(message)
