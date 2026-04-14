import asyncio
import base64
import logging
import time

from eval.config import ConversationConfig
from eval.customer import CustomerLLM
from eval.models import FunctionCallRecord, FunctionResultRecord, TranscriptMessage
from eval.voice import VoiceClient

logger = logging.getLogger(__name__)

SILENCE_DURATION_MS = 1000
SAMPLE_RATE_HZ = 24_000
SAMPLE_WIDTH_BYTES = 2


class ConversationSimulator:
    """Runs a single evaluation scenario end-to-end over the voice pipeline.

    Used as the `target` callable for azure.ai.evaluation.evaluate().
    """

    def __init__(
        self,
        transport_factory,
        voice_client: VoiceClient,
        customer: CustomerLLM,
        conversation_config: ConversationConfig,
    ) -> None:
        self._transport_factory = transport_factory
        self._voice_client = voice_client
        self._customer = customer
        self._config = conversation_config

    async def __call__(self, *, scenario_name: str, instructions: str, **kwargs) -> dict:
        """Run a scenario. Returns a dict consumed by evaluators via column_mapping."""
        try:
            return await self._run(scenario_name, instructions)
        except Exception as e:
            logger.exception("Scenario %s failed", scenario_name)
            return {
                "function_calls": None,
                "transcript": [],
                "agent_switches": [],
                "final_agent": None,
                "turns": 0,
                "error": str(e),
            }

    async def _run(self, scenario_name: str, instructions: str) -> dict:
        logger.info("Starting scenario: %s", scenario_name)

        transcript: list[TranscriptMessage] = []
        function_calls: list[FunctionCallRecord] = []
        function_results: list[FunctionResultRecord] = []
        agent_switches: list[str] = []
        audio_buffer = bytearray()
        current_agent: str | None = None
        turns = 0

        async with self._transport_factory.create() as transport:
            # Start receiving events in background
            receive_queue: asyncio.Queue[dict] = asyncio.Queue()
            receive_done = asyncio.Event()

            async def _receive_loop():
                try:
                    async for event in transport.receive():
                        await receive_queue.put(event)
                except Exception:
                    logger.exception("Receive loop error")
                finally:
                    receive_done.set()

            receive_task = asyncio.create_task(_receive_loop())

            try:
                # Wait for greeting
                await self._collect_agent_turn(
                    receive_queue,
                    receive_done,
                    audio_buffer,
                    transcript,
                    function_calls,
                    function_results,
                    agent_switches,
                    timeout=self._config.greeting_wait_seconds,
                )
                if audio_buffer:
                    text = await self._voice_client.speech_to_text(bytes(audio_buffer))
                    if text:
                        current_agent_name = agent_switches[-1] if agent_switches else "assistant"
                        transcript.append(TranscriptMessage(role=current_agent_name, content=text))
                    audio_buffer.clear()

                current_agent = agent_switches[-1] if agent_switches else None

                # Conversation loop
                while turns < self._config.max_turns:
                    customer_text = await self._customer.generate_response(instructions, transcript)
                    transcript.append(TranscriptMessage(role="user", content=customer_text, timestamp=time.time()))
                    turns += 1

                    # Check exit
                    if any(term in customer_text.lower() for term in ("goodbye", "bye")):
                        logger.info("Customer said goodbye, ending scenario")
                        break

                    # TTS and send
                    async for chunk in self._voice_client.text_to_speech(customer_text, voice=self._config.voice):
                        await transport.send_audio(chunk)

                    # Trailing silence to trigger VAD
                    silence = b"\x00" * (SAMPLE_RATE_HZ * SAMPLE_WIDTH_BYTES * SILENCE_DURATION_MS // 1000)
                    await transport.send_audio(silence)

                    # Collect agent response
                    await self._collect_agent_turn(
                        receive_queue,
                        receive_done,
                        audio_buffer,
                        transcript,
                        function_calls,
                        function_results,
                        agent_switches,
                        timeout=self._config.silence_timeout_seconds,
                    )
                    if audio_buffer:
                        text = await self._voice_client.speech_to_text(bytes(audio_buffer))
                        if text:
                            agent_name = agent_switches[-1] if agent_switches else "assistant"
                            transcript.append(TranscriptMessage(role=agent_name, content=text))
                        audio_buffer.clear()

                    current_agent = agent_switches[-1] if agent_switches else current_agent

            finally:
                receive_task.cancel()
                try:
                    await receive_task
                except asyncio.CancelledError:
                    pass

        logger.info("Scenario %s completed with %d turns", scenario_name, turns)

        # Build conversation for evaluators - skip leading assistant messages (greeting)
        # Azure evaluators expect (user, assistant) pairs starting with user
        eval_messages = []
        for message in transcript:
            if not eval_messages and message.role != "user":
                # Skip leading assistant messages (e.g., greeting)
                continue
            eval_messages.append(
                {"role": "user" if message.role == "user" else "assistant", "content": message.content}
            )

        return {
            "function_calls": [
                {"agent": fc.agent, "plugin": fc.plugin, "function": fc.function} for fc in function_calls
            ],
            # Return full transcript including greeting
            "transcript": [{"role": m.role, "content": m.content} for m in transcript],
            # Azure evaluators need user-first conversation without leading greeting
            "conversation": {"messages": eval_messages},
            "agent_switches": agent_switches,
            "final_agent": current_agent,
            "turns": turns,
            "error": "",
        }

    async def _collect_agent_turn(
        self,
        queue: asyncio.Queue,
        done: asyncio.Event,
        audio_buffer: bytearray,
        transcript: list,
        function_calls: list,
        function_results: list,
        agent_switches: list,
        timeout: float,
    ) -> None:
        """Drain events from the queue until silence timeout, collecting all event types."""
        last_audio_time = time.time()

        while True:
            remaining = timeout - (time.time() - last_audio_time)
            if remaining <= 0:
                break

            try:
                event = await asyncio.wait_for(queue.get(), timeout=min(remaining, 0.5))
            except asyncio.TimeoutError:
                if done.is_set():
                    break
                continue

            kind = event.get("kind")
            data = event.get("data", {})

            if kind == "AudioData":
                audio_b64 = event["audioData"]["data"]
                audio_bytes = base64.b64decode(audio_b64)
                audio_buffer.extend(audio_bytes)
                last_audio_time = time.time()

            elif kind == "Transcription":
                # We handle transcription through audio (transcribe ourselves)
                # but we can still log server-side transcriptions
                pass

            elif kind == "FunctionCall":
                function_calls.append(
                    FunctionCallRecord(
                        agent=data.get("agent", ""),
                        plugin=data.get("plugin", ""),
                        function=data.get("function", ""),
                        arguments=data.get("arguments", ""),
                    )
                )

            elif kind == "FunctionResult":
                function_results.append(
                    FunctionResultRecord(
                        agent=data.get("agent", ""),
                        plugin=data.get("plugin", ""),
                        function=data.get("function", ""),
                        result=data.get("result", ""),
                    )
                )

            elif kind == "AgentSwitch":
                agent_name = data.get("agentName", "")
                if agent_name:
                    agent_switches.append(agent_name)

            elif kind == "StopAudio":
                pass  # Ignore stop signals
