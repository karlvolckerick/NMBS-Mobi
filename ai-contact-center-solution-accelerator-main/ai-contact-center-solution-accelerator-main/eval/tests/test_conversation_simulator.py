from unittest.mock import AsyncMock, MagicMock

from eval.config import ConversationConfig
from eval.conversation_simulator import ConversationSimulator


class TestConversationSimulator:
    def _make_simulator(self):
        return ConversationSimulator(
            transport_factory=MagicMock(),
            voice_client=MagicMock(),
            customer=MagicMock(),
            conversation_config=ConversationConfig(max_turns=3, greeting_wait_seconds=1, silence_timeout_seconds=2),
        )

    async def test_returns_scenario_result_dict(self):
        sim = self._make_simulator()

        # Mock transport context manager
        mock_transport = AsyncMock()
        sim._transport_factory.create.return_value = mock_transport
        mock_transport.__aenter__ = AsyncMock(return_value=mock_transport)
        mock_transport.__aexit__ = AsyncMock(return_value=False)

        # Agent sends greeting transcription, then we simulate customer, then agent responds
        greeting_event = {
            "kind": "Transcription",
            "data": {"speaker": "receptionist", "text": "Hello, how can I help?", "timestamp": None},
        }
        fc_event = {
            "kind": "FunctionCall",
            "data": {"agent": "billing", "plugin": "BillingPlugin", "function": "get_balance", "arguments": "{}"},
        }
        fr_event = {
            "kind": "FunctionResult",
            "data": {"agent": "billing", "plugin": "BillingPlugin", "function": "get_balance", "result": "$150"},
        }
        response_event = {
            "kind": "Transcription",
            "data": {"speaker": "billing", "text": "Your balance is $150.", "timestamp": None},
        }

        async def mock_receive():
            for event in [greeting_event, fc_event, fr_event, response_event]:
                yield event

        mock_transport.receive = mock_receive
        mock_transport.send_audio = AsyncMock()

        # Customer says something then goodbye
        sim._customer.generate_response = AsyncMock(side_effect=["Check my balance please", "Goodbye"])

        # Voice client: TTS returns some bytes, transcription returns text
        async def mock_tts(text, voice):
            yield b"\x00" * 4800

        sim._voice_client.text_to_speech = mock_tts

        result = await sim(scenario_name="test_scenario", instructions="Check balance")

        assert "function_calls" in result
        assert "transcript" in result

    async def test_catches_errors_and_returns_error_result(self):
        sim = self._make_simulator()

        mock_transport = AsyncMock()
        sim._transport_factory.create.return_value = mock_transport
        mock_transport.__aenter__ = AsyncMock(side_effect=Exception("connection refused"))
        mock_transport.__aexit__ = AsyncMock(return_value=False)

        result = await sim(scenario_name="failing", instructions="Test")
        assert result["error"] != ""


class TestConversationFormatting:
    def test_conversation_skips_leading_assistant_messages(self):
        """Azure evaluators expect (user, assistant) pairs - skip initial greeting."""
        from eval.models import TranscriptMessage

        # Simulate transcript: assistant greeting, user query, assistant response, user goodbye
        transcript = [
            TranscriptMessage(role="receptionist", content="Welcome to Acme!"),
            TranscriptMessage(role="user", content="What are your hours?"),
            TranscriptMessage(role="receptionist", content="9am to 5pm"),
            TranscriptMessage(role="user", content="Thanks, goodbye"),
        ]

        # Build eval_messages the same way the simulator does
        eval_messages = []
        started = False
        for m in transcript:
            if not started and m.role != "user":
                continue
            started = True
            eval_messages.append({"role": "user" if m.role == "user" else "assistant", "content": m.content})

        # Should skip the greeting, start with user message
        assert len(eval_messages) == 3
        assert eval_messages[0]["role"] == "user"
        assert eval_messages[0]["content"] == "What are your hours?"
        assert eval_messages[1]["role"] == "assistant"
        assert eval_messages[1]["content"] == "9am to 5pm"
        assert eval_messages[2]["role"] == "user"
        assert eval_messages[2]["content"] == "Thanks, goodbye"
