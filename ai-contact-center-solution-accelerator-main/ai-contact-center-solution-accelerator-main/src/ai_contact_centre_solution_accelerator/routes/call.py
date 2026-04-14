import asyncio
import base64
import json
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, WebSocket
from numpy import ndarray
from semantic_kernel.connectors.ai.open_ai import (
    ListenEvents,
)
from semantic_kernel.contents import AudioContent, ChatHistory, RealtimeAudioEvent, RealtimeTextEvent

from ai_contact_centre_solution_accelerator.agents.agent_factory import create_agents, create_handoffs
from ai_contact_centre_solution_accelerator.auth.dependencies import authenticate_websocket
from ai_contact_centre_solution_accelerator.config import Config, get_config
from ai_contact_centre_solution_accelerator.core.client_factory import (
    create_execution_settings,
    create_realtime_client,
)
from ai_contact_centre_solution_accelerator.core.orchestration import RealtimeHandoffOrchestration

logger = logging.getLogger(__name__)

call_router = APIRouter(tags=["Call"])


def get_attr(obj: Any, path: str, default: Any | None = None) -> Any | None:
    """Safely get a nested attribute by dot path."""
    cur = obj
    for part in path.split("."):
        if cur is None:
            return default
        cur = getattr(cur, part, None)
    return cur if cur is not None else default


async def send_message(websocket: WebSocket, speaker: str, text: str, timestamp: int | None = None):
    """Send a transcription message to the client."""
    try:
        await websocket.send_text(
            json.dumps(
                {
                    "kind": "Transcription",
                    "data": {
                        "speaker": speaker,
                        "text": text,
                        "timestamp": timestamp,
                    },
                }
            )
        )
    except Exception:
        logger.exception("Failed to send Transcription to websocket")


async def send_agent_switch(websocket: WebSocket, agent_name: str):
    """Notify the client that the agent has switched."""
    try:
        await websocket.send_text(
            json.dumps(
                {
                    "kind": "AgentSwitch",
                    "data": {"agentName": agent_name},
                }
            )
        )
    except Exception:
        logger.exception("Failed to send AgentSwitch to websocket")


async def send_function_call(
    websocket: WebSocket,
    agent_name: str,
    plugin_name: str,
    function_name: str,
    arguments: str,
):
    """Send a function call event to the client."""
    if function_name.startswith("transfer_to_"):
        return
    try:
        await websocket.send_text(
            json.dumps(
                {
                    "kind": "FunctionCall",
                    "data": {
                        "agent": agent_name,
                        "plugin": plugin_name,
                        "function": function_name,
                        "arguments": arguments,
                    },
                }
            )
        )
    except Exception:
        logger.exception("Failed to send FunctionCall to websocket")


async def send_function_result(
    websocket: WebSocket,
    agent_name: str,
    plugin_name: str,
    function_name: str,
    result: str,
):
    """Send a function result event to the client."""
    if function_name.startswith("transfer_to_"):
        return
    try:
        await websocket.send_text(
            json.dumps(
                {
                    "kind": "FunctionResult",
                    "data": {
                        "agent": agent_name,
                        "plugin": plugin_name,
                        "function": function_name,
                        "result": result,
                    },
                }
            )
        )
    except Exception:
        logger.exception("Failed to send FunctionResult to websocket")


async def handle_realtime_messages(
    orchestration: RealtimeHandoffOrchestration,
    websocket: WebSocket,
    chat_history: ChatHistory,
    audio_gate: asyncio.Event | None = None,
):
    """Handle messages received from the realtime API."""
    current_agent_name = None
    _greeting_signaled = False

    try:

        async def from_realtime_to_websocket(audio: ndarray):
            """Send audio from the realtime API to the websocket client."""
            await websocket.send_text(
                json.dumps(
                    {
                        "kind": "AudioData",
                        "audioData": {
                            "data": base64.b64encode(audio.tobytes()).decode("utf-8"),
                        },
                    }
                )
            )

        async for event in orchestration.receive(audio_output_callback=from_realtime_to_websocket):
            current_agent = orchestration.get_current_agent()

            # Notify client if agent has switched
            if current_agent and current_agent.name != current_agent_name:
                current_agent_name = current_agent.name
                await send_agent_switch(websocket, current_agent_name)
                logger.info(f"[Switched to {current_agent_name.title()}]")

            match event:
                case RealtimeTextEvent():
                    logger.debug(f"Text event: {event.text.text}")
                case _:
                    service_event = getattr(event, "service_event", None)

                    match event.service_type:
                        case ListenEvents.SESSION_CREATED:
                            logger.info(
                                f"Session Created. Session Id: {get_attr(service_event, 'session.id', '<unknown>')}"
                            )
                        case ListenEvents.SESSION_UPDATED:
                            logger.info("Session updated")
                        case ListenEvents.ERROR:
                            logger.error(f"Session Error: {get_attr(service_event, 'error', '<unknown>')}")
                            chat_history.add_assistant_message("I hit a temporary issue. Please try again.")
                        case ListenEvents.INPUT_AUDIO_BUFFER_SPEECH_STARTED:
                            logger.info(
                                f"Voice activity detection started at {get_attr(service_event, 'audio_start_ms', '<unknown>')} [ms]"
                            )
                            await websocket.send_text(
                                json.dumps({"kind": "StopAudio", "AudioData": None, "StopAudio": {}})
                            )
                        case ListenEvents.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED:
                            user_transcript = get_attr(service_event, "transcript", "")
                            logger.info(f" User:-- {user_transcript}")
                            if user_transcript:
                                chat_history.add_user_message(user_transcript)
                                await send_message(
                                    websocket, "user", user_transcript, get_attr(service_event, "audio_start_ms", 0)
                                )
                        case ListenEvents.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_FAILED:
                            logger.error(f"Transcription Error: {get_attr(service_event, 'error') or '<unknown>'}")
                        case ListenEvents.RESPONSE_AUDIO_TRANSCRIPT_DONE:
                            transcript = get_attr(service_event, "transcript", "")
                            agent_label = current_agent_name.title() if current_agent_name else "AI"
                            logger.info(f" {agent_label}:-- {transcript}")
                            if transcript:
                                chat_history.add_assistant_message(transcript)
                                await send_message(websocket, current_agent_name or "assistant", transcript)
                        case ListenEvents.RESPONSE_DONE:
                            logger.info("Response Done")
                            if not _greeting_signaled and audio_gate is not None:
                                _greeting_signaled = True
                            # After every response, briefly block incoming audio so that
                            # background noise or room echo in the first ~600 ms after the
                            # agent stops speaking cannot trigger an unwanted new turn.
                            if audio_gate is not None:
                                audio_gate.clear()

                                async def _reopen_gate(ev: asyncio.Event = audio_gate) -> None:
                                    await asyncio.sleep(0.6)
                                    ev.set()

                                asyncio.create_task(_reopen_gate())

    except Exception as e:
        logger.exception("Realtime receive loop terminated due to error")
        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "kind": "AgentError",
                        "message": "A tool call failed. The assistant will continue.",
                        "details": str(e),
                    }
                )
            )
        except Exception:
            logger.exception("Failed to send AgentError to websocket")


@call_router.websocket("/ws")
async def agent_connect(
    websocket: WebSocket,
    config: Annotated[Config, Depends(get_config)],
    auth_claims: Annotated[dict | None, Depends(authenticate_websocket)],
):
    """WebSocket endpoint for voice conversations."""
    await websocket.accept()
    logger.info(f"WebSocket connected (auth: {'enabled' if auth_claims else 'disabled'})")

    agents = create_agents(config)
    handoffs = create_handoffs(agents, config)

    execution_settings = create_execution_settings(config)
    realtime_client = create_realtime_client(config)

    chat_history = ChatHistory()

    async def _on_function_call(agent_name: str, function_call):
        """Called when any agent invokes a function."""
        func_name = function_call.function_name or function_call.name
        if not func_name.startswith("transfer_to_"):
            logger.info(f"[🔧 {agent_name.title()} calling: {func_name}]")
        await send_function_call(
            websocket,
            agent_name=agent_name,
            plugin_name=function_call.plugin_name or "",
            function_name=func_name,
            arguments=function_call.arguments or "",
        )

    async def _on_function_result(agent_name: str, function_result):
        """Called when a function returns a result."""
        func_name = function_result.function_name or function_result.name
        if not func_name.startswith("transfer_to_"):
            result_preview = str(function_result.result)[:50]
            if len(str(function_result.result)) > 50:
                result_preview += "..."
            logger.info(f"[✓ Result: {result_preview}]")
        await send_function_result(
            websocket,
            agent_name=agent_name,
            plugin_name=function_result.plugin_name or "",
            function_name=func_name,
            result=str(function_result.result) if function_result.result else "",
        )

    orchestration = RealtimeHandoffOrchestration(
        members=list(agents.values()),
        handoffs=handoffs,
        realtime_client=realtime_client,
        on_function_call=_on_function_call,
        on_function_result=_on_function_result,
        silent_handoffs=config.orchestration.silent_handoffs,
    )

    # audio_gate is cleared while the agent is speaking and for 600 ms after each
    # RESPONSE_DONE. Incoming caller audio is dropped while the gate is closed so
    # that room echo and background noise cannot trigger a new response.
    audio_gate = asyncio.Event()

    async def _greeting_timeout() -> None:
        """Safety valve: unblock audio after 8 s even if RESPONSE_DONE never fires."""
        await asyncio.sleep(8.0)
        audio_gate.set()

    await orchestration.start(settings=execution_settings, create_response=True)
    asyncio.create_task(_greeting_timeout())
    receive_task = asyncio.create_task(handle_realtime_messages(orchestration, websocket, chat_history, audio_gate))

    try:
        while True:
            try:
                stream_data = await websocket.receive_text()
                data = json.loads(stream_data)

                if data["kind"] == "AudioData":
                    # With UNMIXED channel type, ACS sends a 'silent' flag on packets
                    # where no one is speaking. Skip these to avoid feeding empty audio.
                    if data.get("audioData", {}).get("silent"):
                        continue
                    # Block audio while the gate is closed (initial greeting + 600 ms
                    # cooldown after every response) to prevent background noise from
                    # triggering a spurious new turn.
                    if not audio_gate.is_set():
                        continue
                    await orchestration.send(
                        event=RealtimeAudioEvent(
                            audio=AudioContent(
                                data=data["audioData"]["data"],
                                data_format="base64",
                                inner_content=data,
                            ),
                        )
                    )
                else:
                    logger.info(f"Unknown data kind received from websocket: {data['kind']}")

            except Exception as e:
                logger.error(f"Error occurred while processing websocket message: {e}")
                break
    finally:
        receive_task.cancel()
        await orchestration.stop()
