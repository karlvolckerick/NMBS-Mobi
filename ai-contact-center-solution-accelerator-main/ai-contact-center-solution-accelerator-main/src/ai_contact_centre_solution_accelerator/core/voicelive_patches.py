import logging
from copy import deepcopy
from typing import Annotated, Any, Dict, List, Literal, Mapping, Optional, Sequence, Union, override

from openai.types.beta.realtime.session import Tool, Tracing
from openai.types.beta.realtime.session_update_event_param import SessionClientSecret
from pydantic import Field
from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai import SendEvents
from semantic_kernel.connectors.ai.open_ai.services._open_ai_realtime import (
    _create_openai_realtime_client_event,
)
from semantic_kernel.contents import RealtimeEvents, RealtimeFunctionResultEvent, TextContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel

from ai_contact_centre_solution_accelerator.core.realtime_patches import PatchedAzureRealtimeWebsocket

logger: logging.Logger = logging.getLogger(__name__)


class AzureVoiceLiveEndOfUtteranceDetection(KernelBaseModel):
    """End of utterance detection settings.

    Args:
        model: The model to use for end of utterance detection, should be one of the following:
            - semantic_detection_v1
        type: The type of end of utterance detection, should be azure_semantic_vad.
    """

    model: Literal["semantic_detection_v1"] | None = None
    threshold: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    timeout: Annotated[int | None, Field(ge=0)] = None


class AzureVoiceLiveInputAudioNoiseReduction(KernelBaseModel):
    type: Optional[Literal["azure_deep_noise_suppression"]] = None


class AzureVoiceLiveInputAudioEchoCancellation(KernelBaseModel):
    type: Optional[Literal["server_echo_cancellation"]] = None


class AzureVoiceLiveInputAudioTranscription(KernelBaseModel):
    """Input audio transcription settings.

    Args:
        model: The model to use for transcription, should be one of the following:
            - azure-speech
            - gpt-4o-transcribe
            - whisper1
        language: The language for the transcription
        phrase_list: A list of phrases to help the model recognize specific terms or phrases in the audio.
            Currently doesn't support gpt-4o-realtime-preview, gpt-4o-mini-realtime-preview, and phi4-mm-realtime.
    """

    model: Literal["azure-speech", "gpt-4o-transcribe", "whisper1"] | None = None
    language: str | None = None
    phrase_list: Sequence[str] | None = None


class AzureVoiceLiveAnimation(KernelBaseModel):
    """Animation output settings."""

    outputs: Sequence[Literal["viseme_id"]] | None = None
    """Enable animation output by specifying outputs, currently only supports viseme_id."""


class AzureVoiceLiveTurnDetection(KernelBaseModel):
    """Turn detection settings.

    Args:
        type: The type of turn detection, server_vad or azure_semantic_vad.
        create_response: Whether to create a response for each detected turn.
        eagerness: The eagerness of the voice activity detection, can be low, medium, high, or auto,
            used only for semantic_vad.
        interrupt_response: Whether to interrupt the response for each detected turn.
        prefix_padding_ms: The padding before the detected voice activity, in milliseconds.
        silence_duration_ms: The duration of silence to detect the end of a turn, in milliseconds.
        threshold: The threshold for voice activity detection, should be between 0 and 1, only for server_vad.
        remove_filler_words: Whether to remove filler words from the detected turns, only for azure_semantic_vad.
        end_of_utterance_detection: Optional end of utterance detection settings, only for azure_semantic_vad.
    """

    type: Literal["server_vad", "azure_semantic_vad"] = "server_vad"
    create_response: bool | None = None
    eagerness: Literal["low", "medium", "high", "auto"] | None = None
    interrupt_response: bool | None = None
    prefix_padding_ms: Annotated[int | None, Field(ge=0)] = None
    silence_duration_ms: Annotated[int | None, Field(ge=0)] = None
    threshold: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    remove_filler_words: bool | None = None
    end_of_utterance_detection: AzureVoiceLiveEndOfUtteranceDetection | None = None


class AzureVoiceLiveVoiceConfig(KernelBaseModel):
    """Voice settings for Azure Voice Live API.

    Args:
        name: The name of the voice.
        type: The type of voice, either azure-standard or azure-custom.
        temperature: The temperature for the voice, should be between 0.0 and 1.0.
        rate: The speaking rate of the voice, e.g., "1.0" for normal speed.
        endpoint_id: The endpoint ID for the custom voice, if applicable.
        custom_lexicon_url: The URL for a custom lexicon, if applicable.
    """

    name: str | None = None
    type: Literal["azure-standard", "azure-custom"] | None = None
    temperature: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    rate: str | None = None
    endpoint_id: str | None = None
    custom_lexicon_url: str | None = None


class AzureVoiceLiveExecutionSettings(PromptExecutionSettings):
    """Request settings for Azure Voice Live API."""

    modalities: Sequence[Literal["audio", "text"]] | None = None
    ai_model_id: Annotated[str | None, Field(None, serialization_alias="model")] = None
    instructions: str | None = None
    voice: AzureVoiceLiveVoiceConfig | Dict[str, Any] | None = None
    input_audio_sampling_rate: Literal[16000, 24000] | None = None
    input_audio_noise_reduction: AzureVoiceLiveInputAudioNoiseReduction | None = None
    input_audio_echo_cancellation: AzureVoiceLiveInputAudioEchoCancellation | None = None
    input_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] | None = None
    output_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] | None = None
    input_audio_transcription: AzureVoiceLiveInputAudioTranscription | Mapping[str, Any] | None = None
    turn_detection: AzureVoiceLiveTurnDetection | Mapping[str, str] | None = None
    tools: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description="Do not set this manually. It is set by the service based "
            "on the function choice configuration.",
        ),
    ] = None
    tool_choice: Annotated[
        str | None,
        Field(
            description="Do not set this manually. It is set by the service based "
            "on the function choice configuration.",
        ),
    ] = None
    temperature: Annotated[float | None, Field(ge=0.6, le=1.2)] = None
    max_response_output_tokens: Annotated[int | Literal["inf"] | None, Field(gt=0)] = None
    animation: AzureVoiceLiveAnimation | None = None


class AzureVoiceLiveSession(KernelBaseModel):
    """Session configuration for Azure Voice Live API.

    Similar to OpenAI Realtime session with some differences."""

    client_secret: Optional[SessionClientSecret] = None
    input_audio_format: Optional[Literal["pcm16", "g711_ulaw", "g711_alaw"]] = None
    input_audio_noise_reduction: Optional[AzureVoiceLiveInputAudioNoiseReduction] = None
    input_audio_transcription: Optional[AzureVoiceLiveInputAudioTranscription] = None
    input_audio_sampling_rate: Literal[16000, 24000] | None = None
    instructions: Optional[str] = None
    max_response_output_tokens: Union[int, Literal["inf"], None] = None
    modalities: Optional[List[Literal["text", "audio"]]] = None
    model: Optional[str] = None
    output_audio_format: Optional[Literal["pcm16", "g711_ulaw", "g711_alaw"]] = None
    speed: Optional[float] = None
    temperature: Optional[float] = None
    tool_choice: Optional[str] = None
    tools: Optional[List[Tool]] = None
    tracing: Optional[Tracing] = None
    turn_detection: Optional[AzureVoiceLiveTurnDetection] = None
    voice: Optional[AzureVoiceLiveVoiceConfig] = None
    animation: Optional[AzureVoiceLiveAnimation] = None


class PatchedAzureVoiceLiveWebsocket(PatchedAzureRealtimeWebsocket):
    """Azure Voice Live Websocket client."""

    def __init__(self, **kwargs: Any):
        # Voice Live uses a slightly different path structure to OpenAI Realtime
        endpoint = kwargs.get("endpoint")
        if not endpoint:
            raise ValueError("'endpoint' is required to initialize AzureVoiceLiveWebsocket")
        voicelive_ws_endpoint = endpoint.replace("https://", "wss://") + "voice-live"
        # Inject the custom websocket base URL
        kwargs["websocket_base_url"] = voicelive_ws_endpoint
        super().__init__(**kwargs)

    @override
    def get_prompt_execution_settings_class(self) -> type[PromptExecutionSettings]:
        return AzureVoiceLiveExecutionSettings

    @override
    async def send(self, event: RealtimeEvents, **kwargs: Any) -> None:
        """Send an event to the Websocket client.

        We handle conversation.item.create events to ensure they reach the server properly.

        Function result sanitization and session update event with patched settings
        are handled by the patched base class.
        """
        if isinstance(event, RealtimeFunctionResultEvent):
            await super().send(event, **kwargs)
            return

        if event.service_type == SendEvents.CONVERSATION_ITEM_CREATE:
            data = event.service_event or {}
            if not isinstance(data, dict):
                logger.error("Expected dict payload for conversation.item.create, got %s", type(data).__name__)
                return

            item = data.get("item")
            if item is None:
                logger.error("Event data does not contain 'item'")
                return

            # Use explicit role if supplied in the payload, otherwise fall back to the chat message role or system
            role_override = data.get("role")
            payloads: list[dict[str, Any]] = []

            if isinstance(item, ChatMessageContent):
                if role_override is None and getattr(item, "role", None) is not None:
                    role_override = getattr(item.role, "value", None) or getattr(item.role, "name", None)

                for content_item in item.items:
                    if isinstance(content_item, TextContent):
                        payloads.append(
                            {
                                "type": "message",
                                "role": role_override or "system",
                                "content": [
                                    {
                                        "type": "input_text",
                                        "text": content_item.text,
                                    }
                                ],
                            }
                        )
                    else:
                        logger.debug(
                            "Skipping unsupported ChatMessageContent item type '%s' in conversation.item.create",
                            type(content_item).__name__,
                        )
            elif isinstance(item, dict):
                payload_dict = deepcopy(item)
                if not payload_dict.get("role"):
                    payload_dict["role"] = role_override or "system"
                payloads.append(payload_dict)
            elif isinstance(item, str):
                payloads.append(
                    {
                        "type": "message",
                        "role": role_override or "system",
                        "content": [
                            {
                                "type": "input_text",
                                "text": item,
                            }
                        ],
                    }
                )
            else:
                logger.error("Unsupported payload type for conversation.item.create: %s", type(item).__name__)
                return

            for payload in payloads:
                if not payload.get("role"):
                    payload["role"] = role_override or "system"

                await self._send(
                    _create_openai_realtime_client_event(
                        event_type=SendEvents.CONVERSATION_ITEM_CREATE,
                        item=payload,
                    )
                )

            logger.debug("Sent %d conversation.item.create payload(s) to Voice Live", len(payloads))
        else:
            await super().send(event, **kwargs)
