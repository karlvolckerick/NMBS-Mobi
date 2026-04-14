from unittest.mock import patch

from semantic_kernel.functions.kernel_plugin import KernelPlugin

from ai_contact_centre_solution_accelerator.agents.agent_factory import (
    RealtimeAgent,
    create_agent_from_config,
    create_agents,
    create_handoffs,
)
from ai_contact_centre_solution_accelerator.config import load_config


class TestRealtimeAgent:
    def test_create_agent_with_required_fields(self):
        agent = RealtimeAgent(
            name="test_agent",
            description="A test agent",
            instructions="You are a test agent.",
        )

        assert agent.name == "test_agent"
        assert agent.description == "A test agent"
        assert agent.instructions == "You are a test agent."
        assert agent.kernel is not None

    def test_create_agent_with_voice(self):
        agent = RealtimeAgent(
            name="test_agent",
            description="A test agent",
            instructions="Test",
            voice="shimmer",
        )

        assert agent.voice == "shimmer"

    def test_create_agent_with_plugins(self):
        plugin = KernelPlugin(name="test_plugin", functions=[])

        agent = RealtimeAgent(
            name="test_agent",
            description="A test agent",
            instructions="Test",
            plugins={"test_plugin": plugin},
        )

        assert agent.kernel is not None

    def test_agent_str_representation(self):
        agent = RealtimeAgent(
            name="test_agent",
            description="A test agent",
        )

        str_repr = str(agent)
        assert "test_agent" in str_repr
        assert "A test agent" in str_repr

    def test_agent_id_is_generated(self):
        agent = RealtimeAgent(
            name="test_agent",
            description="A test agent",
        )

        assert agent.id is not None
        assert len(agent.id) > 0

    def test_agent_custom_id(self):
        agent = RealtimeAgent(
            id="custom-id-123",
            name="test_agent",
            description="A test agent",
        )

        assert agent.id == "custom-id-123"


class TestAgentFactory:
    def test_create_agent_from_config(self, config_with_agents):
        config = load_config(config_with_agents)
        agent_config = config.agents[0]

        with patch(
            "ai_contact_centre_solution_accelerator.agents.agent_factory.load_plugins_for_agent", return_value=[]
        ):
            agent = create_agent_from_config(agent_config, config)

        assert agent.name == "receptionist"
        assert agent.description == "A friendly receptionist"
        assert agent.voice == "alloy"

    def test_create_agents_from_config(self, config_with_agents):
        config = load_config(config_with_agents)

        with patch(
            "ai_contact_centre_solution_accelerator.agents.agent_factory.load_plugins_for_agent", return_value=[]
        ):
            agents = create_agents(config)

        assert len(agents) == 2
        assert "receptionist" in agents
        assert "billing" in agents
        assert isinstance(agents["receptionist"], RealtimeAgent)
        assert isinstance(agents["billing"], RealtimeAgent)

    def test_create_handoffs_from_config(self, config_with_agents):
        config = load_config(config_with_agents)

        with patch(
            "ai_contact_centre_solution_accelerator.agents.agent_factory.load_plugins_for_agent", return_value=[]
        ):
            agents = create_agents(config)
            handoffs = create_handoffs(agents, config)

        assert handoffs is not None

        receptionist_handoffs = handoffs.get("receptionist")
        assert receptionist_handoffs is not None
        assert "billing" in receptionist_handoffs

        billing_handoffs = handoffs.get("billing")
        assert billing_handoffs is not None
        assert "receptionist" in billing_handoffs

    def test_create_handoffs_empty_config(self, minimal_config):
        config = load_config(minimal_config)

        agents = create_agents(config)
        handoffs = create_handoffs(agents, config)

        assert len(list(handoffs.items())) == 0
