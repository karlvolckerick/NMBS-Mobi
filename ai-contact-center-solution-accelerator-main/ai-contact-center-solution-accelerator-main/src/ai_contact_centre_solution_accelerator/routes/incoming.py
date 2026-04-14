import logging
import uuid
from typing import Annotated
from urllib.parse import urlencode

from azure.communication.callautomation import (
    AudioFormat,
    CallAutomationClient,
    MediaStreamingAudioChannelType,
    MediaStreamingContentType,
    MediaStreamingOptions,
    StreamingTransportType,
)
from azure.eventgrid import EventGridEvent, SystemEventNames
from fastapi import APIRouter, Depends, Request

from ai_contact_centre_solution_accelerator.config import Config, get_config

logger = logging.getLogger(__name__)
incoming_call_router = APIRouter(tags=["Incoming Calls"])

_acs_client: CallAutomationClient | None = None


def get_acs_client(config: Annotated[Config, Depends(get_config)]) -> CallAutomationClient:
    global _acs_client
    if _acs_client is None:
        connection_string = config.acs.connection_string.get_secret_value()
        if not connection_string:
            raise ValueError("ACS configuration is required. Set ACS_CONNECTION_STRING environment variable.")
        _acs_client = CallAutomationClient.from_connection_string(connection_string)
    return _acs_client


@incoming_call_router.post("/calls/incoming")
async def incoming_call_handler(
    request: Request,
    config: Annotated[Config, Depends(get_config)],
    acs_client: Annotated[CallAutomationClient, Depends(get_acs_client)],
):
    events = await request.json()
    logger.info(f"Received {len(events)} event(s)")

    for event_dict in events:
        event_type = event_dict.get("eventType", "Unknown")
        logger.info(f"Processing event: {event_type}")

        try:
            event = EventGridEvent.from_dict(event_dict)

            if event.event_type == SystemEventNames.EventGridSubscriptionValidationEventName:
                validation_code = event.data["validationCode"]
                logger.info("Returning Event Grid validation response")
                return {"validationResponse": validation_code}

            if event.event_type == SystemEventNames.AcsIncomingCallEventName:
                caller_id = (
                    event.data["from"]["phoneNumber"]["value"]
                    if event.data["from"]["kind"] == "phoneNumber"
                    else event.data["from"]["rawId"]
                )
                logger.info(f"Incoming call from: {caller_id}")

                incoming_call_context = event.data["incomingCallContext"]
                call_id = str(uuid.uuid4())
                query_params = urlencode({"callerId": caller_id})

                callback_uri = f"https://{config.acs.callback_host}/calls/events/{call_id}?{query_params}"
                websocket_uri = f"wss://{config.acs.callback_host}/ws?{query_params}"

                logger.info(f"Answering call with WebSocket URI: {websocket_uri}")

                answer_result = acs_client.answer_call(
                    incoming_call_context=incoming_call_context,
                    callback_url=callback_uri,
                    media_streaming=MediaStreamingOptions(
                        transport_url=websocket_uri,
                        transport_type=StreamingTransportType.WEBSOCKET,
                        content_type=MediaStreamingContentType.AUDIO,
                        audio_channel_type=MediaStreamingAudioChannelType.UNMIXED,
                        start_media_streaming=True,
                        enable_bidirectional=True,
                        audio_format=AudioFormat.PCM24_K_MONO,
                    ),
                )
                logger.info(f"Call answered: {answer_result.call_connection_id}")

        except Exception as e:
            logger.exception(f"Error processing event: {e}")

    return {"status": "ok"}


@incoming_call_router.post("/calls/events/{call_id}")
async def call_events_handler(call_id: str, request: Request):
    events = await request.json()

    for event in events:
        event_type = event.get("type", "Unknown")
        event_data = event.get("data", {})
        call_connection_id = event_data.get("callConnectionId", "")

        logger.info(f"Call event: {event_type}, call_id={call_id}, connection={call_connection_id}")

        if event_type == "Microsoft.Communication.CallDisconnected":
            logger.info(f"Call disconnected: {call_connection_id}")

    return {"status": "ok"}
