from unittest.mock import AsyncMock, MagicMock

import pytest

from eval.voice import SAMPLE_RATE_HZ, VoiceClient


class TestVoiceClientTTS:
    async def test_text_to_speech_returns_pcm_bytes(self):
        async def mock_iter_bytes():
            yield b"\x00" * 9600
            yield b"\x00" * 4800

        mock_response = AsyncMock()
        mock_response.iter_bytes = mock_iter_bytes

        mock_streaming = AsyncMock()
        mock_streaming.__aenter__ = AsyncMock(return_value=mock_response)
        mock_streaming.__aexit__ = AsyncMock(return_value=False)

        mock_speech = MagicMock()
        mock_speech.with_streaming_response.create = MagicMock(return_value=mock_streaming)

        mock_client = MagicMock()
        mock_client.audio.speech = mock_speech

        client = VoiceClient(openai_client=mock_client, tts_deployment="tts", transcription_deployment="transcribe")
        chunks = []
        async for chunk in client.text_to_speech("Hello world", voice="alloy"):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert all(isinstance(c, bytes) for c in chunks)

    async def test_text_to_speech_raises_on_empty_text(self):
        mock_client = MagicMock()
        client = VoiceClient(openai_client=mock_client, tts_deployment="tts", transcription_deployment="transcribe")

        with pytest.raises(ValueError, match="empty"):
            async for _ in client.text_to_speech("", voice="alloy"):
                pass


class TestVoiceClientTranscription:
    async def test_speech_to_text(self):
        mock_transcriptions = AsyncMock()
        mock_transcriptions.create = AsyncMock(return_value="Hello world")

        mock_client = MagicMock()
        mock_client.audio.transcriptions = mock_transcriptions

        client = VoiceClient(openai_client=mock_client, tts_deployment="tts", transcription_deployment="transcribe")

        # Create valid PCM audio (24kHz, 16-bit, mono)
        pcm_data = b"\x00" * (SAMPLE_RATE_HZ * 2)  # 1 second of silence
        result = await client.speech_to_text(pcm_data)

        assert result == "Hello world"
        mock_transcriptions.create.assert_awaited_once()

        # Verify the file argument is a WAV
        call_kwargs = mock_transcriptions.create.call_args.kwargs
        file_tuple = call_kwargs["file"]
        assert file_tuple[0] == "audio.wav"

    async def test_speech_to_text_empty_response(self):
        mock_transcriptions = AsyncMock()
        mock_transcriptions.create = AsyncMock(return_value="  ")

        mock_client = MagicMock()
        mock_client.audio.transcriptions = mock_transcriptions

        client = VoiceClient(openai_client=mock_client, tts_deployment="tts", transcription_deployment="transcribe")

        result = await client.speech_to_text(b"\x00" * 100)
        assert result == ""
