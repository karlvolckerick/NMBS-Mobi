from unittest.mock import AsyncMock, MagicMock

from eval.customer import CustomerLLM
from eval.models import TranscriptMessage


class TestCustomerLLM:
    async def test_generate_response(self):
        mock_choice = MagicMock()
        mock_choice.message.content = "I'd like to check my balance please."

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        customer = CustomerLLM(openai_client=mock_client, chat_deployment="gpt-4o")
        result = await customer.generate_response(
            instructions="You want to check your account balance.",
            transcript=[
                TranscriptMessage(role="assistant", content="Hello, how can I help you today?"),
            ],
        )

        assert result == "I'd like to check my balance please."
        mock_client.chat.completions.create.assert_awaited_once()

    async def test_generate_response_empty_returns_fallback(self):
        mock_choice = MagicMock()
        mock_choice.message.content = ""

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        customer = CustomerLLM(openai_client=mock_client, chat_deployment="gpt-4o")
        result = await customer.generate_response(
            instructions="You want to check your balance.",
            transcript=[
                TranscriptMessage(role="assistant", content="Hello!"),
            ],
        )

        assert result == "Could you repeat that?"

    async def test_builds_prompt_from_transcript(self):
        mock_choice = MagicMock()
        mock_choice.message.content = "Sure, it's SW1A 1AA."

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        customer = CustomerLLM(openai_client=mock_client, chat_deployment="gpt-4o")
        await customer.generate_response(
            instructions="You want to check your balance. Your postcode is SW1A 1AA.",
            transcript=[
                TranscriptMessage(role="assistant", content="Hello, how can I help?"),
                TranscriptMessage(role="user", content="I want to check my balance."),
                TranscriptMessage(role="assistant", content="Can I have your postcode?"),
            ],
        )

        call_args = mock_client.chat.completions.create.call_args.kwargs
        messages = call_args["messages"]
        assert messages[0]["role"] == "system"
        assert "SW1A 1AA" in messages[0]["content"]
        assert "Assistant: Hello, how can I help?" in messages[1]["content"]
