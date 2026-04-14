import json
from unittest.mock import AsyncMock, patch

import pytest

from eval.transport import WebSocketTransport


class TestWebSocketTransport:
    async def test_connect_and_disconnect(self):
        mock_ws = AsyncMock()
        with patch("eval.transport.websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
            transport = WebSocketTransport(url="ws://localhost:8000/ws")
            async with transport:
                assert transport.is_connected
            mock_ws.close.assert_awaited_once()

    async def test_send_audio(self):
        mock_ws = AsyncMock()
        with patch("eval.transport.websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
            transport = WebSocketTransport(url="ws://localhost:8000/ws")
            async with transport:
                await transport.send_audio(b"\x00\x01\x02\x03")

                mock_ws.send.assert_awaited_once()
                sent = json.loads(mock_ws.send.call_args[0][0])
                assert sent["kind"] == "AudioData"
                assert "data" in sent["audioData"]

    async def test_receive_dispatches_audio(self):
        audio_msg = json.dumps({"kind": "AudioData", "audioData": {"data": "AAEC"}})
        mock_ws = AsyncMock()

        async def async_messages():
            yield audio_msg

        mock_ws.__aiter__ = lambda self: async_messages()
        mock_ws.close = AsyncMock()

        with patch("eval.transport.websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
            transport = WebSocketTransport(url="ws://localhost:8000/ws")
            async with transport:
                events = []
                async for event in transport.receive():
                    events.append(event)

                assert len(events) == 1
                assert events[0]["kind"] == "AudioData"

    async def test_receive_dispatches_function_call(self):
        fc_msg = json.dumps(
            {
                "kind": "FunctionCall",
                "data": {"agent": "billing", "plugin": "BillingPlugin", "function": "get_balance", "arguments": "{}"},
            }
        )
        mock_ws = AsyncMock()

        async def async_messages():
            yield fc_msg

        mock_ws.__aiter__ = lambda self: async_messages()
        mock_ws.close = AsyncMock()

        with patch("eval.transport.websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
            transport = WebSocketTransport(url="ws://localhost:8000/ws")
            async with transport:
                events = []
                async for event in transport.receive():
                    events.append(event)

                assert events[0]["kind"] == "FunctionCall"
                assert events[0]["data"]["plugin"] == "BillingPlugin"

    async def test_receive_dispatches_agent_switch(self):
        switch_msg = json.dumps({"kind": "AgentSwitch", "data": {"agentName": "billing"}})
        mock_ws = AsyncMock()

        async def async_messages():
            yield switch_msg

        mock_ws.__aiter__ = lambda self: async_messages()
        mock_ws.close = AsyncMock()

        with patch("eval.transport.websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
            transport = WebSocketTransport(url="ws://localhost:8000/ws")
            async with transport:
                events = []
                async for event in transport.receive():
                    events.append(event)

                assert events[0]["kind"] == "AgentSwitch"

    async def test_send_raises_when_not_connected(self):
        transport = WebSocketTransport(url="ws://localhost:8000/ws")
        with pytest.raises(RuntimeError, match="not connected"):
            await transport.send_audio(b"\x00")

    async def test_headers_passed_to_connect(self):
        mock_ws = AsyncMock()
        with patch("eval.transport.websockets.connect", new_callable=AsyncMock, return_value=mock_ws) as mock_connect:
            transport = WebSocketTransport(
                url="ws://localhost:8000/ws",
                headers={"Authorization": "Bearer token"},
            )
            async with transport:
                pass

            mock_connect.assert_awaited_once()
            call_kwargs = mock_connect.call_args
            assert call_kwargs.kwargs.get("additional_headers") == {"Authorization": "Bearer token"}
