import io
import logging
import wave
from collections.abc import AsyncIterator

from openai import AsyncAzureOpenAI

logger = logging.getLogger(__name__)

SAMPLE_RATE_HZ = 24_000
SAMPLE_WIDTH_BYTES = 2  # 16-bit PCM
CHANNELS = 1
BYTES_PER_CHUNK = 9600  # ~200ms at 24kHz 16-bit mono


class VoiceClient:
    """TTS and transcription using Azure OpenAI."""

    def __init__(
        self,
        openai_client: AsyncAzureOpenAI,
        tts_deployment: str,
        transcription_deployment: str,
    ) -> None:
        self._client = openai_client
        self._tts_deployment = tts_deployment
        self._transcription_deployment = transcription_deployment

    async def text_to_speech(self, text: str, voice: str) -> AsyncIterator[bytes]:
        """Convert text to PCM audio chunks via Azure OpenAI TTS.

        Yields PCM 24kHz 16-bit mono chunks.
        """
        if not text or not text.strip():
            raise ValueError("text is empty")

        buffer = b""
        async with self._client.audio.speech.with_streaming_response.create(
            model=self._tts_deployment,
            voice=voice,
            input=text,
            response_format="pcm",
        ) as response:
            async for chunk in response.iter_bytes():
                buffer += chunk
                while len(buffer) >= BYTES_PER_CHUNK:
                    yield buffer[:BYTES_PER_CHUNK]
                    buffer = buffer[BYTES_PER_CHUNK:]
        if buffer:
            yield buffer

    async def speech_to_text(self, pcm_data: bytes) -> str:
        """Convert PCM audio to text via Azure OpenAI transcription."""
        wav_bytes = io.BytesIO()
        with wave.open(wav_bytes, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(SAMPLE_WIDTH_BYTES)
            wf.setframerate(SAMPLE_RATE_HZ)
            wf.writeframes(pcm_data)
        wav_bytes.seek(0)

        file_tuple = ("audio.wav", wav_bytes, "audio/wav")
        response = await self._client.audio.transcriptions.create(
            model=self._transcription_deployment,
            file=file_tuple,
            response_format="text",
        )
        return response.strip() if response else ""
