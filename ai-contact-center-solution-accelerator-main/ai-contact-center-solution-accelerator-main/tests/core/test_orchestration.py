from unittest.mock import AsyncMock, MagicMock

import pytest
from semantic_kernel.agents.orchestration.handoffs import OrchestrationHandoffs
from semantic_kernel.connectors.ai.open_ai import OpenAIRealtimeExecutionSettings
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.realtime_events import RealtimeFunctionCallEvent

from ai_contact_centre_solution_accelerator.agents.realtime_agent import RealtimeAgent
from ai_contact_centre_solution_accelerator.core.orchestration import RealtimeHandoffOrchestration
from ai_contact_centre_solution_accelerator.core.voicelive_patches import (
    AzureVoiceLiveExecutionSettings,
    AzureVoiceLiveTurnDetection,
    AzureVoiceLiveVoiceConfig,
)


class TestRealtimeAgentInOrchestration:
    def test_agent_with_description(self):
        agent = RealtimeAgent(
            name="receptionist",
            description="A friendly receptionist",
            instructions="You are a receptionist.",
            voice="alloy",
        )

        assert agent.name == "receptionist"
        assert agent.description == "A friendly receptionist"
        assert agent.voice == "alloy"

    def test_agent_without_description(self):
        agent = RealtimeAgent(
            name="test",
            instructions="Test",
        )

        assert agent.name == "test"
        assert agent.description is None

    def test_multiple_agents_for_orchestration(self):
        receptionist = RealtimeAgent(
            name="receptionist",
            description="A friendly receptionist",
            instructions="You are a receptionist.",
            voice="alloy",
        )
        billing = RealtimeAgent(
            name="billing",
            description="A billing specialist",
            instructions="You are a billing specialist.",
            voice="echo",
        )

        agents = {"receptionist": receptionist, "billing": billing}

        assert len(agents) == 2
        assert agents["receptionist"].voice == "alloy"
        assert agents["billing"].voice == "echo"


class TestOrchestrationHandoffsSetup:
    def test_create_handoffs(self):
        receptionist = RealtimeAgent(
            name="receptionist",
            description="A friendly receptionist",
            instructions="You are a receptionist.",
        )
        billing = RealtimeAgent(
            name="billing",
            description="A billing specialist",
            instructions="You are a billing specialist.",
        )

        handoffs = OrchestrationHandoffs()
        handoffs.add(receptionist, billing, "Transfer to billing")
        handoffs.add(billing, receptionist, "Transfer to receptionist")

        receptionist_handoffs = handoffs.get("receptionist")
        assert receptionist_handoffs is not None
        assert "billing" in receptionist_handoffs

        billing_handoffs = handoffs.get("billing")
        assert billing_handoffs is not None
        assert "receptionist" in billing_handoffs

    def test_empty_handoffs(self):
        handoffs = OrchestrationHandoffs()

        assert len(list(handoffs.items())) == 0


class TestOrchestrationValidation:
    def test_agent_map_creation(self):
        agents = [
            RealtimeAgent(
                name="receptionist",
                description="A receptionist",
                instructions="Test",
            ),
            RealtimeAgent(
                name="billing",
                description="A billing specialist",
                instructions="Test",
            ),
        ]

        agent_map = {agent.name: agent for agent in agents}

        assert len(agent_map) == 2
        assert "receptionist" in agent_map
        assert "billing" in agent_map

    def test_get_agent_by_name(self):
        agents = [
            RealtimeAgent(
                name="receptionist",
                description="A receptionist",
                instructions="Test",
            ),
        ]

        agent_map = {agent.name: agent for agent in agents}

        agent = agent_map.get("receptionist")
        assert agent is not None
        assert agent.name == "receptionist"

        missing = agent_map.get("nonexistent")
        assert missing is None


class TestBuildSettingsForAgent:
    @pytest.fixture
    def orchestration(self):
        receptionist = RealtimeAgent(
            name="receptionist",
            description="A friendly receptionist",
            instructions="You are a receptionist.",
            voice="alloy",
        )
        billing = RealtimeAgent(
            name="billing",
            description="A billing specialist",
            instructions="You are a billing specialist.",
            voice="echo",
        )

        handoffs = OrchestrationHandoffs()
        handoffs.add(receptionist, billing, "Transfer to billing")
        handoffs.add(billing, receptionist, "Transfer to receptionist")

        mock_client = MagicMock()
        mock_client.create_session = AsyncMock()

        return RealtimeHandoffOrchestration(
            members=[receptionist, billing],
            handoffs=handoffs,
            realtime_client=mock_client,
            silent_handoffs=False,
        )

    def test_without_base_settings_creates_openai_settings(self, orchestration):
        agent = orchestration.current_agent
        settings = orchestration._build_settings_for_agent(agent)

        assert isinstance(settings, OpenAIRealtimeExecutionSettings)
        assert settings.instructions == agent.instructions
        assert settings.voice == agent.voice

    def test_with_base_settings_preserves_type(self, orchestration):
        agent = orchestration.current_agent
        base_settings = AzureVoiceLiveExecutionSettings(
            turn_detection=AzureVoiceLiveTurnDetection(type="server_vad"),
            voice=AzureVoiceLiveVoiceConfig(name="en-US-AvaNeural"),
        )

        settings = orchestration._build_settings_for_agent(agent, base_settings=base_settings)

        assert isinstance(settings, AzureVoiceLiveExecutionSettings)

    def test_with_base_settings_preserves_turn_detection(self, orchestration):
        agent = orchestration.current_agent
        turn_detection = AzureVoiceLiveTurnDetection(
            type="azure_semantic_vad",
            eagerness="high",
        )
        base_settings = AzureVoiceLiveExecutionSettings(turn_detection=turn_detection)

        settings = orchestration._build_settings_for_agent(agent, base_settings=base_settings)

        assert settings.turn_detection is not None
        assert settings.turn_detection.type == "azure_semantic_vad"
        assert settings.turn_detection.eagerness == "high"

    def test_with_base_settings_updates_voice_name_from_agent(self, orchestration):
        agent = orchestration.current_agent
        voice_config = AzureVoiceLiveVoiceConfig(
            name="en-US-AvaNeural",
            type="azure-standard",
            rate="1.2",
        )
        base_settings = AzureVoiceLiveExecutionSettings(voice=voice_config)

        settings = orchestration._build_settings_for_agent(agent, base_settings=base_settings)

        assert settings.voice is not None
        assert settings.voice.name == agent.voice
        assert settings.voice.type == "azure-standard"
        assert settings.voice.rate == "1.2"

    def test_with_base_settings_preserves_voice_when_agent_has_no_voice(self, orchestration):
        agent = orchestration.current_agent
        agent.voice = None
        voice_config = AzureVoiceLiveVoiceConfig(
            name="en-US-AvaNeural",
            type="azure-standard",
            rate="1.2",
        )
        base_settings = AzureVoiceLiveExecutionSettings(voice=voice_config)

        settings = orchestration._build_settings_for_agent(agent, base_settings=base_settings)

        assert settings.voice is not None
        assert settings.voice.name == "en-US-AvaNeural"
        assert settings.voice.rate == "1.2"

    def test_with_base_settings_updates_instructions(self, orchestration):
        agent = orchestration.current_agent
        base_settings = AzureVoiceLiveExecutionSettings(
            instructions="Old instructions",
            voice=AzureVoiceLiveVoiceConfig(name="en-US-AvaNeural"),
        )

        settings = orchestration._build_settings_for_agent(agent, base_settings=base_settings)

        assert settings.instructions == agent.instructions

    def test_base_settings_not_mutated(self, orchestration):
        agent = orchestration.current_agent
        original_instructions = "Original instructions"
        base_settings = AzureVoiceLiveExecutionSettings(
            instructions=original_instructions,
            voice=AzureVoiceLiveVoiceConfig(name="en-US-AvaNeural"),
        )

        orchestration._build_settings_for_agent(agent, base_settings=base_settings)

        assert base_settings.instructions == original_instructions


class TestSilentHandoffInstructions:
    @pytest.fixture
    def orchestration(self):
        receptionist = RealtimeAgent(
            name="receptionist",
            description="A friendly receptionist",
            instructions="You are a receptionist.",
            voice="alloy",
        )
        billing = RealtimeAgent(
            name="billing",
            description="A billing specialist",
            instructions="You are a billing specialist.",
            voice="echo",
        )

        handoffs = OrchestrationHandoffs()
        handoffs.add(receptionist, billing, "Transfer to billing")
        handoffs.add(billing, receptionist, "Transfer to receptionist")

        mock_client = MagicMock()
        mock_client.create_session = AsyncMock()

        return RealtimeHandoffOrchestration(
            members=[receptionist, billing],
            handoffs=handoffs,
            realtime_client=mock_client,
            silent_handoffs=True,
        )

    def test_silent_handoff_suffix_forbids_transfer_announcements(self, orchestration):
        suffix = orchestration._get_silent_handoff_instruction_suffix(pending_query="What's my balance?")

        assert "NEVER mention being transferred" in suffix
        assert "NEVER say 'Transferred to" in suffix

    def test_silent_handoff_suffix_without_query_is_lightweight(self, orchestration):
        suffix = orchestration._get_silent_handoff_instruction_suffix()

        assert "CRITICAL CONVERSATION RULES" in suffix
        assert "CURRENT CONTEXT" not in suffix

    def test_silent_handoff_suffix_includes_pending_query_context(self, orchestration):
        suffix = orchestration._get_silent_handoff_instruction_suffix(pending_query="What payment methods do you take?")

        assert "What payment methods do you take?" in suffix
        assert "Do NOT ask them to repeat" in suffix

    def test_build_settings_appends_silent_handoff_suffix(self, orchestration):
        agent = orchestration.current_agent
        settings = orchestration._build_settings_for_agent(agent)

        assert "CRITICAL CONVERSATION RULES" in settings.instructions

    def test_build_settings_includes_pending_query_in_suffix(self, orchestration):
        agent = orchestration.current_agent
        settings = orchestration._build_settings_for_agent(agent, pending_query="What's my balance?")

        assert "What's my balance?" in settings.instructions
        assert "Do NOT ask them to repeat" in settings.instructions


class TestSwitchToAgent:
    @pytest.fixture
    def orchestration(self):
        receptionist = RealtimeAgent(
            name="receptionist",
            description="A friendly receptionist",
            instructions="You are a receptionist.",
            voice="alloy",
        )
        billing = RealtimeAgent(
            name="billing",
            description="A billing specialist",
            instructions="You are a billing specialist.",
            voice="echo",
        )

        handoffs = OrchestrationHandoffs()
        handoffs.add(receptionist, billing, "Transfer to billing")
        handoffs.add(billing, receptionist, "Transfer to receptionist")

        mock_client = MagicMock()
        mock_client.create_session = AsyncMock()
        mock_client.update_session = AsyncMock()

        return RealtimeHandoffOrchestration(
            members=[receptionist, billing],
            handoffs=handoffs,
            realtime_client=mock_client,
            silent_handoffs=True,
        )

    @pytest.mark.asyncio
    async def test_switch_auto_responds_when_pending_query_exists(self, orchestration):
        orchestration._last_user_query = "What payment methods do you take?"
        billing = orchestration._agent_map["billing"]

        await orchestration._switch_to_agent(billing)

        orchestration.realtime_client.update_session.assert_called_once()
        call_kwargs = orchestration.realtime_client.update_session.call_args[1]
        assert call_kwargs["create_response"] is True

    @pytest.mark.asyncio
    async def test_switch_does_not_auto_respond_when_no_pending_query(self, orchestration):
        orchestration._last_user_query = None
        billing = orchestration._agent_map["billing"]

        await orchestration._switch_to_agent(billing)

        orchestration.realtime_client.update_session.assert_called_once()
        call_kwargs = orchestration.realtime_client.update_session.call_args[1]
        assert call_kwargs["create_response"] is False

    @pytest.mark.asyncio
    async def test_switch_does_not_auto_respond_when_silent_handoffs_disabled(self, orchestration):
        orchestration.silent_handoffs = False
        orchestration._last_user_query = "What payment methods do you take?"
        billing = orchestration._agent_map["billing"]

        await orchestration._switch_to_agent(billing)

        orchestration.realtime_client.update_session.assert_called_once()
        call_kwargs = orchestration.realtime_client.update_session.call_args[1]
        assert call_kwargs["create_response"] is False

    @pytest.mark.asyncio
    async def test_switch_updates_current_agent(self, orchestration):
        billing = orchestration._agent_map["billing"]
        assert orchestration.current_agent.name == "receptionist"

        await orchestration._switch_to_agent(billing)

        assert orchestration.current_agent.name == "billing"


class TestFunctionCallDeduplication:
    @pytest.fixture
    def orchestration(self):
        receptionist = RealtimeAgent(
            name="receptionist",
            description="A friendly receptionist",
            instructions="You are a receptionist.",
            voice="alloy",
        )
        billing = RealtimeAgent(
            name="billing",
            description="A billing specialist",
            instructions="You are a billing specialist.",
            voice="echo",
        )

        handoffs = OrchestrationHandoffs()
        handoffs.add(receptionist, billing, "Transfer to billing")

        mock_client = MagicMock()
        mock_client.create_session = AsyncMock()

        return RealtimeHandoffOrchestration(
            members=[receptionist, billing],
            handoffs=handoffs,
            realtime_client=mock_client,
            silent_handoffs=False,
        )

    def _make_function_call_event(self, call_id: str, function_name: str = "get_balance"):
        fc = FunctionCallContent(
            id=call_id,
            name=function_name,
            function_name=function_name,
            plugin_name="billing",
            arguments="{}",
            metadata={"call_id": call_id},
        )
        return RealtimeFunctionCallEvent(function_call=fc)

    @pytest.mark.asyncio
    async def test_callback_fires_once_per_call_id(self, orchestration):
        callback = AsyncMock()
        orchestration.on_function_call = callback
        orchestration._is_started = True

        event = self._make_function_call_event("call_1")

        async def fake_receive(**kwargs):
            # Simulate the same call_id arriving multiple times (streaming deltas)
            yield event
            yield event
            yield event

        orchestration.realtime_client.receive = fake_receive

        async for _ in orchestration.receive():
            pass

        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_fires_for_each_distinct_call_id(self, orchestration):
        callback = AsyncMock()
        orchestration.on_function_call = callback
        orchestration._is_started = True

        event_a = self._make_function_call_event("call_1", "get_balance")
        event_b = self._make_function_call_event("call_2", "get_orders")

        async def fake_receive(**kwargs):
            yield event_a
            yield event_a  # duplicate of call_1
            yield event_b
            yield event_b  # duplicate of call_2

        orchestration.realtime_client.receive = fake_receive

        async for _ in orchestration.receive():
            pass

        assert callback.call_count == 2


class TestStopClearsPendingFunctionCalls:
    @pytest.fixture
    def orchestration(self):
        receptionist = RealtimeAgent(
            name="receptionist",
            description="A friendly receptionist",
            instructions="You are a receptionist.",
            voice="alloy",
        )
        billing = RealtimeAgent(
            name="billing",
            description="A billing specialist",
            instructions="You are a billing specialist.",
            voice="echo",
        )

        handoffs = OrchestrationHandoffs()
        handoffs.add(receptionist, billing, "Transfer to billing")

        mock_client = MagicMock()
        mock_client.create_session = AsyncMock()
        mock_client.close_session = AsyncMock()

        return RealtimeHandoffOrchestration(
            members=[receptionist, billing],
            handoffs=handoffs,
            realtime_client=mock_client,
            silent_handoffs=False,
        )

    @pytest.mark.asyncio
    async def test_stop_clears_pending_function_calls(self, orchestration):
        orchestration._is_started = True
        orchestration._pending_function_calls["call_1"] = FunctionCallContent(id="call_1", name="get_balance")
        orchestration._pending_function_calls["call_2"] = FunctionCallContent(id="call_2", name="get_orders")

        await orchestration.stop()

        assert orchestration._pending_function_calls == {}
