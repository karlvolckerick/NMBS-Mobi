"""
Patches for Azure OpenAI Realtime WebSocket client.

This module contains workarounds for known issues in the Semantic Kernel
Azure Realtime client.
"""

import logging
from typing import Any, override

from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai import AzureRealtimeWebsocket, SendEvents
from semantic_kernel.contents import ImageContent, RealtimeEvents, RealtimeFunctionResultEvent, TextContent
from semantic_kernel.contents.binary_content import BinaryContent

logger: logging.Logger = logging.getLogger(__name__)


class PatchedAzureRealtimeWebsocket(AzureRealtimeWebsocket):
    """Azure Realtime Websocket client with centralized function result sanitization.

    Ensures function tool results are strings to prevent hanging in the realtime service.
    """

    def __init__(
        self,
        *,
        endpoint: str,
        deployment_name: str | None = None,
        ad_token_provider: Any | None = None,
        api_key: str | None = None,
        api_version: str | None = None,
        plugins: list[Any] = [],
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            endpoint=endpoint,
            deployment_name=deployment_name,
            ad_token_provider=ad_token_provider,
            api_key=api_key,
            api_version=api_version,
            plugins=plugins,
            settings=settings,
            **kwargs,
        )

    @staticmethod
    def _sanitize_function_result(event: RealtimeEvents) -> None:
        """Sanitize function results to ensure they are strings.

        The Azure OpenAI Realtime API expects function results to be strings.
        If they are other types, the service may hang indefinitely.
        See: https://github.com/microsoft/semantic-kernel/issues/13003
        """
        if isinstance(event, RealtimeFunctionResultEvent):
            result = event.function_result.result
            if isinstance(result, list):
                if len(result) > 0 and isinstance(result[0], TextContent):
                    serialized_res = result[0].text
                elif len(result) > 0 and isinstance(result[0], ImageContent):
                    serialized_res = result[0].data_uri
                elif len(result) > 0 and isinstance(result[0], BinaryContent):
                    serialized_res = result[0].data_string
                else:
                    serialized_res = str(result)
            else:
                serialized_res = str(event.function_result)

            event.function_result.result = serialized_res

    async def _patched_session_update(self, event: RealtimeEvents, **kwargs: Any) -> None:
        """Send a SESSION_UPDATE event with proper handling.

        Handles the modified session update event due to OpenAI SDK expecting
        different execution settings.
        """
        if event.service_type != SendEvents.SESSION_UPDATE:
            raise ValueError("Event should be of type SESSION_UPDATE.")

        data = event.service_event
        if not data:
            logger.error("Event data is empty")
            return

        settings = data.get("settings", None)
        if not settings:
            logger.error("Event data does not contain 'settings'")
            return

        try:
            settings = self.get_prompt_execution_settings_from_settings(settings)
        except Exception as e:
            logger.error(f"Failed to create settings: {settings}, error: {e}")
            return

        assert isinstance(settings, self.get_prompt_execution_settings_class())  # nosec

        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id

        await self._send(
            {
                "type": SendEvents.SESSION_UPDATE.value,
                "session": settings.prepare_settings_dict(),  # type: ignore
            }
        )

    @override
    async def send(self, event: RealtimeEvents, **kwargs: Any) -> None:
        """Send an event to the realtime service with function result sanitization."""
        self._sanitize_function_result(event)

        if event.service_type == SendEvents.SESSION_UPDATE:
            await self._patched_session_update(event, **kwargs)
        else:
            await super().send(event, **kwargs)
