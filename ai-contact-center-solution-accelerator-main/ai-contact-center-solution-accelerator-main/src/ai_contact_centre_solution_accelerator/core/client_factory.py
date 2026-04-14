from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from semantic_kernel.connectors.ai.open_ai import (
    AzureRealtimeExecutionSettings,
    InputAudioTranscription,
    TurnDetection,
)

from ai_contact_centre_solution_accelerator.config import Config
from ai_contact_centre_solution_accelerator.core.realtime_patches import PatchedAzureRealtimeWebsocket
from ai_contact_centre_solution_accelerator.core.voicelive_patches import (
    AzureVoiceLiveAnimation,
    AzureVoiceLiveExecutionSettings,
    AzureVoiceLiveInputAudioEchoCancellation,
    AzureVoiceLiveInputAudioNoiseReduction,
    AzureVoiceLiveInputAudioTranscription,
    AzureVoiceLiveTurnDetection,
    AzureVoiceLiveVoiceConfig,
    PatchedAzureVoiceLiveWebsocket,
)

# Shared credential instance — reused across WebSocket connections so that the
# Managed Identity token is cached after the first fetch (~3 s) instead of being
# re-fetched from scratch on every reconnect, which was pushing setup time past
# uvicorn's 20-second WebSocket ping timeout and causing 1011 disconnects.
_shared_credential: DefaultAzureCredential | None = None


def _get_shared_credential() -> DefaultAzureCredential:
    global _shared_credential
    if _shared_credential is None:
        _shared_credential = DefaultAzureCredential()
    return _shared_credential


def create_realtime_client(config: Config) -> PatchedAzureRealtimeWebsocket:
    """Create the appropriate realtime client based on config.

    Args:
        config: Application configuration.

    Returns:
        PatchedAzureVoiceLiveWebsocket if client_type is voicelive,
        PatchedAzureRealtimeWebsocket otherwise.
    """
    ad_token_provider = get_bearer_token_provider(
        _get_shared_credential(),
        "https://cognitiveservices.azure.com/.default",
    )

    if config.azure_openai.client_type == "voicelive":
        return PatchedAzureVoiceLiveWebsocket(
            endpoint=config.azure_openai.endpoint,
            deployment_name=config.azure_openai.deployment,
            ad_token_provider=ad_token_provider,
            api_version=config.azure_openai.api_version,
        )
    else:
        return PatchedAzureRealtimeWebsocket(
            endpoint=config.azure_openai.endpoint,
            deployment_name=config.azure_openai.deployment,
            ad_token_provider=ad_token_provider,
            api_version=config.azure_openai.api_version,
        )


def create_execution_settings(config: Config) -> AzureRealtimeExecutionSettings:
    """Create execution settings based on config and client type.

    Args:
        config: Application configuration.

    Returns:
        AzureVoiceLiveExecutionSettings if client_type is voicelive,
        AzureRealtimeExecutionSettings otherwise.
    """
    if config.azure_openai.client_type == "voicelive":
        return _create_voicelive_settings(config)
    else:
        return _create_realtime_settings(config)


def _create_realtime_settings(config: Config) -> AzureRealtimeExecutionSettings:
    """Create standard realtime execution settings."""
    return AzureRealtimeExecutionSettings(
        input_audio_transcription=InputAudioTranscription(
            model=config.azure_openai.transcription_model,
            language="en",
        ),
        turn_detection=TurnDetection(
            type=config.turn_detection.type,
            create_response=config.turn_detection.create_response,
            silence_duration_ms=config.turn_detection.silence_duration_ms,
            threshold=config.turn_detection.threshold,
        ),
    )


def _create_voicelive_settings(config: Config) -> AzureVoiceLiveExecutionSettings:
    """Create Voice Live execution settings from config."""
    voice_live_config = config.voicelive

    if voice_live_config.semantic_vad.enabled:
        turn_detection = AzureVoiceLiveTurnDetection(
            type="azure_semantic_vad",
            create_response=config.turn_detection.create_response,
            eagerness=voice_live_config.semantic_vad.eagerness,
            interrupt_response=voice_live_config.semantic_vad.interrupt_response,
            remove_filler_words=voice_live_config.semantic_vad.remove_filler_words,
        )
    else:
        turn_detection = AzureVoiceLiveTurnDetection(
            type=config.turn_detection.type,
            create_response=config.turn_detection.create_response,
            silence_duration_ms=config.turn_detection.silence_duration_ms,
            threshold=config.turn_detection.threshold,
        )

    noise_reduction = None
    if voice_live_config.noise_reduction.enabled:
        noise_reduction = AzureVoiceLiveInputAudioNoiseReduction(type="azure_deep_noise_suppression")

    echo_cancellation = None
    if voice_live_config.echo_cancellation.enabled:
        echo_cancellation = AzureVoiceLiveInputAudioEchoCancellation(type="server_echo_cancellation")

    voice = AzureVoiceLiveVoiceConfig(
        name=config.voice.default,
        type=voice_live_config.voice.type,
        rate=voice_live_config.voice.rate,
        temperature=voice_live_config.voice.temperature,
        endpoint_id=voice_live_config.voice.endpoint_id or None,
        custom_lexicon_url=voice_live_config.voice.custom_lexicon_url or None,
    )

    animation = None
    if voice_live_config.animation.viseme_enabled:
        animation = AzureVoiceLiveAnimation(outputs=["viseme_id"])

    # Belgian station names to help azure-speech transcribe them correctly.
    # Without this, similar-sounding English words override them (e.g. Leuven -> London).
    _STATION_PHRASE_LIST = [
        "Leuven", "Antwerpen-Centraal", "Brussel-Centraal", "Gent-Sint-Pieters",
        "Brugge", "Liège-Guillemins", "Mechelen", "Hasselt", "Kortrijk", "Namur",
        "Namen", "Charleroi", "Luik", "Turnhout", "Genk", "Aalst", "Dendermonde",
        "Roeselare", "Sint-Niklaas", "Aarschot", "Lier", "Tongeren", "Waremme",
        "Ottignies", "Mons", "La Louvière", "Verviers", "Visé", "Dinant",
    ]

    return AzureVoiceLiveExecutionSettings(
        input_audio_transcription=AzureVoiceLiveInputAudioTranscription(
            model=config.azure_openai.transcription_model,
            language="en",
            phrase_list=_STATION_PHRASE_LIST,
        ),
        turn_detection=turn_detection,
        input_audio_noise_reduction=noise_reduction,
        input_audio_echo_cancellation=echo_cancellation,
        voice=voice,
        animation=animation,
    )
