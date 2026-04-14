from unittest.mock import MagicMock, patch

from semantic_kernel.connectors.ai.open_ai import AzureRealtimeExecutionSettings

from ai_contact_centre_solution_accelerator.core.client_factory import create_execution_settings, create_realtime_client
from ai_contact_centre_solution_accelerator.core.realtime_patches import PatchedAzureRealtimeWebsocket
from ai_contact_centre_solution_accelerator.core.voicelive_patches import (
    AzureVoiceLiveExecutionSettings,
    PatchedAzureVoiceLiveWebsocket,
)


class TestCreateRealtimeClient:
    def test_returns_voicelive_client_by_default(self):
        mock_config = MagicMock()
        mock_config.azure_openai.client_type = "voicelive"
        mock_config.azure_openai.endpoint = "https://test.openai.azure.com/"
        mock_config.azure_openai.deployment = "gpt-4o-realtime"
        mock_config.azure_openai.api_version = "2024-10-01-preview"

        with patch("ai_contact_centre_solution_accelerator.core.client_factory.get_bearer_token_provider"):
            with patch("ai_contact_centre_solution_accelerator.core.client_factory.DefaultAzureCredential"):
                client = create_realtime_client(mock_config)
                assert isinstance(client, PatchedAzureVoiceLiveWebsocket)

    def test_returns_realtime_client_when_configured(self):
        mock_config = MagicMock()
        mock_config.azure_openai.client_type = "realtime"
        mock_config.azure_openai.endpoint = "https://test.openai.azure.com/"
        mock_config.azure_openai.deployment = "gpt-4o-realtime"
        mock_config.azure_openai.api_version = "2024-10-01-preview"

        with patch("ai_contact_centre_solution_accelerator.core.client_factory.get_bearer_token_provider"):
            with patch("ai_contact_centre_solution_accelerator.core.client_factory.DefaultAzureCredential"):
                client = create_realtime_client(mock_config)
                assert isinstance(client, PatchedAzureRealtimeWebsocket)
                assert not isinstance(client, PatchedAzureVoiceLiveWebsocket)


class TestCreateExecutionSettings:
    def test_returns_realtime_settings_when_realtime(self):
        mock_config = MagicMock()
        mock_config.azure_openai.client_type = "realtime"
        mock_config.azure_openai.transcription_model = "gpt-4o-transcribe"
        mock_config.turn_detection.type = "server_vad"
        mock_config.turn_detection.create_response = True
        mock_config.turn_detection.silence_duration_ms = 800
        mock_config.turn_detection.threshold = 0.8

        settings = create_execution_settings(mock_config)

        assert isinstance(settings, AzureRealtimeExecutionSettings)
        assert settings.turn_detection.type == "server_vad"

    def test_returns_voicelive_settings_with_defaults(self):
        mock_config = MagicMock()
        mock_config.azure_openai.client_type = "voicelive"
        mock_config.azure_openai.transcription_model = "gpt-4o-transcribe"
        mock_config.turn_detection.type = "server_vad"
        mock_config.turn_detection.create_response = True
        mock_config.turn_detection.silence_duration_ms = 800
        mock_config.turn_detection.threshold = 0.8

        mock_config.voice.default = "en-US-AvaMultilingualNeural"
        mock_config.voicelive.noise_reduction.enabled = True
        mock_config.voicelive.echo_cancellation.enabled = True
        mock_config.voicelive.semantic_vad.enabled = False
        mock_config.voicelive.voice.type = "azure-standard"
        mock_config.voicelive.voice.rate = "1.0"
        mock_config.voicelive.voice.temperature = 0.8
        mock_config.voicelive.voice.endpoint_id = ""
        mock_config.voicelive.voice.custom_lexicon_url = ""
        mock_config.voicelive.animation.viseme_enabled = False

        settings = create_execution_settings(mock_config)

        assert isinstance(settings, AzureVoiceLiveExecutionSettings)
        assert settings.input_audio_noise_reduction is not None
        assert settings.input_audio_noise_reduction.type == "azure_deep_noise_suppression"
        assert settings.input_audio_echo_cancellation is not None
        assert settings.input_audio_echo_cancellation.type == "server_echo_cancellation"

    def test_voicelive_settings_with_semantic_vad(self):
        mock_config = MagicMock()
        mock_config.azure_openai.client_type = "voicelive"
        mock_config.azure_openai.transcription_model = "gpt-4o-transcribe"
        mock_config.turn_detection.type = "server_vad"
        mock_config.turn_detection.create_response = True
        mock_config.turn_detection.silence_duration_ms = 800
        mock_config.turn_detection.threshold = 0.8

        mock_config.voice.default = "en-US-AvaMultilingualNeural"
        mock_config.voicelive.noise_reduction.enabled = True
        mock_config.voicelive.echo_cancellation.enabled = True
        mock_config.voicelive.semantic_vad.enabled = True
        mock_config.voicelive.semantic_vad.eagerness = "high"
        mock_config.voicelive.semantic_vad.remove_filler_words = True
        mock_config.voicelive.voice.type = "azure-standard"
        mock_config.voicelive.voice.rate = "1.0"
        mock_config.voicelive.voice.temperature = 0.8
        mock_config.voicelive.voice.endpoint_id = ""
        mock_config.voicelive.voice.custom_lexicon_url = ""
        mock_config.voicelive.animation.viseme_enabled = False

        settings = create_execution_settings(mock_config)

        assert settings.turn_detection.type == "azure_semantic_vad"
        assert settings.turn_detection.eagerness == "high"
