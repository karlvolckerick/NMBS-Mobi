"""
RealtimeHandoffOrchestration - Multi-agent orchestration for realtime voice conversations.

This orchestration manages multiple RealtimeAgents sharing a single realtime session,
handling handoffs between agents via function calling.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable, Coroutine
from functools import partial
from typing import Any

from numpy import ndarray
from pydantic import Field, PrivateAttr
from semantic_kernel.agents.orchestration.handoffs import HANDOFF_PLUGIN_NAME, AgentHandoffs, OrchestrationHandoffs
from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_calling_utils import prepare_settings_for_function_calling
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_realtime_execution_settings import (
    OpenAIRealtimeExecutionSettings,
)
from semantic_kernel.connectors.ai.realtime_client_base import RealtimeClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.connectors.ai.open_ai.services._open_ai_realtime import SendEvents
from semantic_kernel.contents.realtime_events import (
    RealtimeEvent,
    RealtimeEvents,
    RealtimeFunctionCallEvent,
    RealtimeFunctionResultEvent,
)
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel

from ai_contact_centre_solution_accelerator.agents.realtime_agent import RealtimeAgent
from ai_contact_centre_solution_accelerator.config import get_config
from ai_contact_centre_solution_accelerator.core.mcp_loader import get_mcp_plugins_for_agent

logger = logging.getLogger(__name__)

# Type aliases for callbacks
FunctionCallCallback = Callable[[str, FunctionCallContent], Awaitable[None] | None]
FunctionResultCallback = Callable[[str, FunctionResultContent], Awaitable[None] | None]


class RealtimeHandoffOrchestration(KernelBaseModel):
    """Orchestrates multiple RealtimeAgents sharing a single realtime session.

    This orchestration enables multi-agent voice conversations where agents can
    hand off to each other using function calling. All agents share the same
    realtime session - when a handoff occurs, the session is updated with the
    new agent's instructions and tools.

    Attributes:
        members: List of RealtimeAgents participating in the orchestration.
        handoffs: Defines which agents can hand off to which other agents.
        realtime_client: The shared realtime client (WebSocket or WebRTC).
        current_agent: The currently active agent.
        on_function_call: Optional callback invoked when a function is called.
        on_function_result: Optional callback invoked when a function returns.
        silent_handoffs: If True (default), handoffs are seamless without user notification.
    """

    model_config = {"arbitrary_types_allowed": True}

    members: list[RealtimeAgent] = Field(default_factory=list)
    handoffs: OrchestrationHandoffs = Field(default_factory=OrchestrationHandoffs)
    realtime_client: Any  # RealtimeClientBase - typed as Any for testing flexibility
    current_agent: RealtimeAgent | None = None
    on_function_call: FunctionCallCallback | None = Field(default=None, exclude=True)
    on_function_result: FunctionResultCallback | None = Field(default=None, exclude=True)
    silent_handoffs: bool = Field(default=True)

    _agent_map: dict[str, RealtimeAgent] = PrivateAttr(default_factory=dict)
    _is_started: bool = PrivateAttr(default=False)
    _handoff_pending: str | None = PrivateAttr(default=None)
    _agent_kernels: dict[str, Kernel] = PrivateAttr(default_factory=dict)
    _pending_function_calls: dict[str, FunctionCallContent] = PrivateAttr(default_factory=dict)
    _last_user_query: str | None = PrivateAttr(default=None)
    _base_execution_settings: OpenAIRealtimeExecutionSettings | None = PrivateAttr(default=None)

    def __init__(
        self,
        members: list[RealtimeAgent],
        handoffs: OrchestrationHandoffs,
        realtime_client: RealtimeClientBase,
        on_function_call: FunctionCallCallback | None = None,
        on_function_result: FunctionResultCallback | None = None,
        silent_handoffs: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize the RealtimeHandoffOrchestration.

        Args:
            members: List of RealtimeAgents participating in the orchestration.
            handoffs: Defines the handoff connections between agents.
            realtime_client: The shared realtime client.
            on_function_call: Optional callback invoked when any agent calls a function.
            on_function_result: Optional callback invoked when any function returns.
            silent_handoffs: If True (default), agents will NOT announce handoffs.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            members=members,
            handoffs=handoffs,
            realtime_client=realtime_client,
            on_function_call=on_function_call,
            on_function_result=on_function_result,
            silent_handoffs=silent_handoffs,
            **kwargs,
        )
        self._validate_configuration()
        self._build_agent_map()
        self._build_agent_kernels_with_handoffs()

        if self.members:
            self.current_agent = self.members[0]

    def _validate_configuration(self) -> None:
        """Validate the orchestration configuration."""
        if not self.members:
            raise ValueError("Members list cannot be empty.")

        if not self.handoffs:
            raise ValueError("Handoffs cannot be empty.")

        member_names = {m.name for m in self.members}

        for member in self.members:
            if not member.description:
                raise ValueError(f"Agent '{member.name}' must have a description.")

        for agent_name, connections in self.handoffs.items():
            if agent_name not in member_names:
                raise ValueError(f"Agent '{agent_name}' in handoffs is not a member.")
            for target_name in connections:
                if target_name not in member_names:
                    raise ValueError(f"Handoff target '{target_name}' is not a member.")
                if target_name == agent_name:
                    raise ValueError(f"Agent '{agent_name}' cannot hand off to itself.")

    def _build_agent_map(self) -> None:
        """Build a mapping from agent names to agent instances."""
        self._agent_map = {agent.name: agent for agent in self.members}

    def _build_agent_kernels_with_handoffs(self) -> None:
        """Build kernels for each agent with their handoff functions added.

        MCP plugins are added here (after cloning) because they contain async state
        that cannot be deep copied. This ensures each agent gets the shared MCP
        plugin instances without attempting to clone them.
        """
        config = get_config()
        for agent in self.members:
            kernel = agent.kernel.clone()

            mcp_plugins = get_mcp_plugins_for_agent(agent.name, config)
            for plugin in mcp_plugins:
                kernel.add_plugin(plugin)

            handoff_connections = self.handoffs.get(agent.name, AgentHandoffs())

            if handoff_connections:
                self._add_handoff_functions_to_kernel(kernel, handoff_connections)

            self._agent_kernels[agent.name] = kernel

    def _add_handoff_functions_to_kernel(self, kernel: Kernel, handoff_connections: AgentHandoffs) -> None:
        """Add handoff functions to a kernel based on the agent's connections."""
        functions: list[KernelFunctionFromMethod] = []

        for target_agent_name, handoff_description in handoff_connections.items():
            function_name = f"transfer_to_{target_agent_name}"

            if self.silent_handoffs:
                function_description = (
                    f"Immediately and silently route the conversation to the {target_agent_name} specialist "
                    f"when the user's needs match: {handoff_description or target_agent_name}. "
                    f"CRITICAL: Call this function WITHOUT saying anything first. "
                    f"Do NOT generate any text before calling this function."
                )
            else:
                function_description = handoff_description or f"Transfer the conversation to {target_agent_name}"

            return_parameter = KernelParameterMetadata(
                name="return",
                description="",
                default_value=None,
                type_="None",
                type_object=None,
                is_required=False,
            )

            function_metadata = KernelFunctionMetadata(
                name=function_name,
                description=function_description,
                parameters=[],
                return_parameter=return_parameter,
                is_prompt=False,
                is_asynchronous=True,
                plugin_name=HANDOFF_PLUGIN_NAME,
                additional_properties={},
            )

            functions.append(
                KernelFunctionFromMethod.model_construct(
                    metadata=function_metadata,
                    method=partial(self._handoff_to_agent, target_agent_name),
                )
            )

        if functions:
            kernel.add_plugin(plugin=KernelPlugin(name=HANDOFF_PLUGIN_NAME, functions=functions))

    async def _handoff_to_agent(self, agent_name: str) -> str:
        """Mark a handoff to another agent."""
        logger.info(f"Handoff requested to agent: {agent_name}")
        self._handoff_pending = agent_name

        if self.silent_handoffs:
            return "OK"
        else:
            return f"Transferring conversation to {agent_name}"

    def _get_silent_handoff_instruction_suffix(self, pending_query: str | None = None) -> str:
        """Get the instruction suffix for silent handoffs."""
        base_instructions = (
            "\n\n## CRITICAL CONVERSATION RULES ##\n"
            "You are part of a unified assistant system. The user MUST perceive they are talking to ONE assistant.\n\n"
            "RULE 1 - WHEN HANDING OFF:\n"
            "- Call transfer functions IMMEDIATELY with NO preceding text\n"
            "- FORBIDDEN: 'Let me transfer you', 'I'll connect you', 'One moment'\n\n"
            "RULE 2 - WHEN RESPONDING AFTER A HANDOFF:\n"
            "- You may have just received this conversation from another part of the system\n"
            "- NEVER mention being transferred, handed off, or being a different specialist\n"
            "- NEVER say 'Transferred to...', 'I'm the billing specialist', etc.\n"
            "- FORBIDDEN: Greetings like 'Hi', 'Hello', 'Hey'\n"
            "- REQUIRED: Answer the user's question DIRECTLY as if you were always part of the conversation\n"
        )

        if pending_query:
            base_instructions += (
                f"\n\n## CURRENT CONTEXT ##\n"
                f'The user just asked: "{pending_query}"\n'
                f"Answer this question immediately and directly. Do NOT ask them to repeat it."
            )

        return base_instructions

    def _build_settings_for_agent(
        self,
        agent: RealtimeAgent,
        pending_query: str | None = None,
        base_settings: OpenAIRealtimeExecutionSettings | None = None,
    ) -> OpenAIRealtimeExecutionSettings:
        """Build execution settings for an agent including their tools.

        Args:
            agent: The agent to build settings for.
            pending_query: Optional pending user query for context.
            base_settings: Optional base settings to use. If provided, agent-specific
                settings (instructions, voice, tools) will be merged into a copy of these
                settings. This allows preserving VoiceLive-specific settings like
                turn_detection, noise_reduction, etc.

        Returns:
            Execution settings configured for the agent.
        """
        instructions = agent.instructions
        if self.silent_handoffs:
            instructions = (instructions or "") + self._get_silent_handoff_instruction_suffix(pending_query)

        if base_settings:
            settings = base_settings.model_copy(deep=True)
            settings.instructions = instructions
            # For VoiceLive, update the voice name within the AzureVoiceLiveVoiceConfig
            # if the agent has a different voice specified
            if agent.voice and hasattr(settings, "voice") and settings.voice is not None:
                # Check if this is a VoiceLive voice config (has 'name' attribute)
                if hasattr(settings.voice, "name"):
                    settings.voice.name = agent.voice
        else:
            settings = OpenAIRealtimeExecutionSettings(
                instructions=instructions,
                voice=agent.voice,
            )

        kernel = self._agent_kernels.get(agent.name, agent.kernel)

        if agent.function_choice_behavior:
            settings.function_choice_behavior = agent.function_choice_behavior
            settings = prepare_settings_for_function_calling(
                settings,
                type(settings),
                self._update_function_choice_settings_callback(),
                kernel=kernel,
            )

        return settings

    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[[FunctionCallChoiceConfiguration, OpenAIRealtimeExecutionSettings, FunctionChoiceType], None]:
        """Return the callback function to update settings from function call configuration."""
        from semantic_kernel.connectors.ai.open_ai.services._open_ai_realtime import (
            update_settings_from_function_call_configuration,
        )

        return update_settings_from_function_call_configuration

    async def _switch_to_agent(self, agent: RealtimeAgent) -> None:
        """Switch the session to a new agent."""
        logger.info(f"Switching to agent: {agent.name}")

        # Cancel any in-progress response from the current agent so its audio
        # does not overlap with the new agent's audio. This is particularly
        # important when the caller is speaking a non-English language: the LLM
        # may start speaking in that language AND call a transfer function at the
        # same time, causing two agents to talk simultaneously.
        try:
            await self.realtime_client.send(RealtimeEvent(service_type=SendEvents.RESPONSE_CANCEL))
            logger.info("Sent response.cancel before agent switch")
        except Exception as e:
            logger.warning(f"Could not cancel in-progress response before switch: {e}")

        self.current_agent = agent
        settings = self._build_settings_for_agent(
            agent, pending_query=self._last_user_query, base_settings=self._base_execution_settings
        )
        kernel = self._agent_kernels.get(agent.name, agent.kernel)

        # When silent handoffs are enabled and there's a pending user query,
        # trigger an automatic response so the new agent answers immediately
        # instead of waiting for the user to repeat themselves.
        should_auto_respond = self.silent_handoffs and self._last_user_query is not None

        # Immediately swap instructions/tools so the new agent is ready.
        await self.realtime_client.update_session(
            settings=settings,
            kernel=kernel,
            create_response=False,
        )

        # Wait for ACS to drain any audio that was already buffered before the
        # cancel. Non-English responses can be longer so we use a slightly
        # longer window (2.5 s) instead of the previous 1.5 s to avoid overlap.
        if should_auto_respond:
            await asyncio.sleep(2.5)
            await self.realtime_client.update_session(
                settings=settings,
                kernel=kernel,
                create_response=True,
            )

        logger.info(f"Agent switch complete: {agent.name}")

    async def start(
        self,
        chat_history: ChatHistory | None = None,
        settings: OpenAIRealtimeExecutionSettings | None = None,
        **kwargs: Any,
    ) -> None:
        """Start the orchestration and create the realtime session.

        Args:
            chat_history: Optional chat history to initialize the session with.
            settings: Base execution settings (e.g., AzureVoiceLiveExecutionSettings or
                AzureRealtimeExecutionSettings). Agent-specific settings like instructions
                and tools will be merged into these settings.
            **kwargs: Additional keyword arguments passed to create_session.
        """
        if self._is_started:
            raise RuntimeError("Orchestration is already started.")

        if not self.current_agent:
            raise RuntimeError("No agents configured in orchestration.")

        self._base_execution_settings = settings

        agent_settings = self._build_settings_for_agent(self.current_agent, base_settings=settings)

        kernel = self._agent_kernels.get(self.current_agent.name, self.current_agent.kernel)

        await self.realtime_client.create_session(
            chat_history=chat_history,
            settings=agent_settings,
            kernel=kernel,
            **kwargs,
        )

        self._is_started = True
        logger.info(f"Orchestration started with agent: {self.current_agent.name}")

    async def stop(self) -> None:
        """Stop the orchestration and close the realtime session."""
        if self._is_started:
            await self.realtime_client.close_session()
            self._is_started = False
            self._pending_function_calls.clear()
            logger.info("Orchestration stopped.")

    async def receive(
        self,
        audio_output_callback: Callable[[ndarray], Coroutine[Any, Any, None]] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[RealtimeEvents, None]:
        """Receive events from the realtime session, handling handoffs and function calls."""
        if not self._is_started:
            raise RuntimeError("Orchestration is not started. Call start() first.")

        async for event in self.realtime_client.receive(
            audio_output_callback=audio_output_callback,
            **kwargs,
        ):
            # Track the last user query
            if hasattr(event, "service_type") and hasattr(event, "service_event"):
                from semantic_kernel.connectors.ai.open_ai.services._open_ai_realtime import ListenEvents

                if event.service_type == ListenEvents.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED.value:
                    service_event = event.service_event
                    if hasattr(service_event, "transcript") and service_event.transcript:
                        self._last_user_query = service_event.transcript

            # Track function calls
            if isinstance(event, RealtimeFunctionCallEvent):
                function_name = event.function_call.function_name or event.function_call.name
                call_id = event.function_call.metadata.get("call_id") if event.function_call.metadata else None

                is_new_call = call_id and call_id not in self._pending_function_calls

                if call_id:
                    self._pending_function_calls[call_id] = event.function_call

                if function_name and function_name.startswith("transfer_to_"):
                    target_agent_name = function_name.replace("transfer_to_", "")
                    if target_agent_name in self._agent_map:
                        self._handoff_pending = target_agent_name

                if is_new_call and self.on_function_call and self.current_agent:
                    try:
                        result = self.on_function_call(self.current_agent.name, event.function_call)
                        if result is not None and hasattr(result, "__await__"):
                            await result
                    except Exception as e:
                        logger.error(f"Error in on_function_call callback: {e}")

            # Track function results
            if isinstance(event, RealtimeFunctionResultEvent):
                call_id = event.function_result.metadata.get("call_id") if event.function_result.metadata else None

                if call_id and call_id in self._pending_function_calls:
                    del self._pending_function_calls[call_id]

                if self.on_function_result and self.current_agent:
                    try:
                        result = self.on_function_result(self.current_agent.name, event.function_result)
                        if result is not None and hasattr(result, "__await__"):
                            await result
                    except Exception as e:
                        logger.error(f"Error in on_function_result callback: {e}")

                # Handle pending handoff
                if self._handoff_pending:
                    target_agent = self._agent_map.get(self._handoff_pending)
                    if target_agent:
                        self._handoff_pending = None
                        yield event
                        await self._switch_to_agent(target_agent)
                        continue

            yield event

    async def send(self, event: RealtimeEvents, **kwargs: Any) -> None:
        """Send an event to the realtime session."""
        if not self._is_started:
            raise RuntimeError("Orchestration is not started. Call start() first.")

        await self.realtime_client.send(event, **kwargs)

    async def __aenter__(self) -> "RealtimeHandoffOrchestration":
        """Enter the async context manager."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the async context manager."""
        await self.stop()

    def get_current_agent(self) -> RealtimeAgent | None:
        """Get the currently active agent."""
        return self.current_agent

    def get_agent_by_name(self, name: str) -> RealtimeAgent | None:
        """Get an agent by name."""
        return self._agent_map.get(name)

    def is_handoff_pending(self) -> bool:
        """Check if a handoff is currently pending."""
        return self._handoff_pending is not None
