"""Tests for VoiceLive WebSocket client patches."""

from unittest.mock import AsyncMock

from semantic_kernel.connectors.ai.open_ai import SendEvents
from semantic_kernel.contents import RealtimeFunctionResultEvent, TextContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.realtime_events import RealtimeEvent
from semantic_kernel.contents.utils.author_role import AuthorRole

from ai_contact_centre_solution_accelerator.core.voicelive_patches import PatchedAzureVoiceLiveWebsocket


class TestVoiceLiveFunctionResultHandling:
    async def test_sends_function_result_as_function_call_output(self):
        client = PatchedAzureVoiceLiveWebsocket(
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4o-realtime",
            ad_token_provider=lambda: "test-token",
            api_version="2024-10-01-preview",
        )
        client._send = AsyncMock()

        function_result = FunctionResultContent(
            id="test-id",
            plugin_name="BillingPlugin",
            function_name="get_account_balance",
            result="Balance: $100",
            metadata={"call_id": "call_123"},
        )
        event = RealtimeFunctionResultEvent(
            service_type=SendEvents.CONVERSATION_ITEM_CREATE,
            function_result=function_result,
        )

        await client.send(event)

        sent_event = client._send.call_args[0][0]
        assert sent_event.item.type == "function_call_output"
        assert sent_event.item.call_id == "call_123"
        assert sent_event.item.output == "Balance: $100"

    async def test_sends_text_conversation_item_as_system_message(self):
        client = PatchedAzureVoiceLiveWebsocket(
            endpoint="https://test.openai.azure.com/",
            deployment_name="gpt-4o-realtime",
            ad_token_provider=lambda: "test-token",
            api_version="2024-10-01-preview",
        )
        client._send = AsyncMock()

        text_message = ChatMessageContent(
            role=AuthorRole.SYSTEM,
            items=[TextContent(text="Your balance is $100.")],
        )
        event = RealtimeEvent(
            service_type=SendEvents.CONVERSATION_ITEM_CREATE,
            service_event={"item": text_message},
        )

        await client.send(event)

        sent_event = client._send.call_args[0][0]
        assert sent_event.item.type == "message"
        assert sent_event.item.role == "system"
