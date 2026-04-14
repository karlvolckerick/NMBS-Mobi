"""
Agent factory for creating and configuring agents from config.yaml.

This module provides functions to create agents and configure their handoffs
based on the YAML configuration file.
"""

import logging

from semantic_kernel.agents.orchestration.handoffs import OrchestrationHandoffs

from ai_contact_centre_solution_accelerator.agents.realtime_agent import RealtimeAgent
from ai_contact_centre_solution_accelerator.config import AgentConfig, Config, get_config
from ai_contact_centre_solution_accelerator.tools.loader import load_plugins_for_agent

logger = logging.getLogger(__name__)


def create_agent_from_config(agent_config: AgentConfig, config: Config) -> RealtimeAgent:
    """Create a RealtimeAgent from an AgentConfig.

    Args:
        agent_config: The agent configuration from config.yaml.
        config: The full configuration object.

    Returns:
        A configured RealtimeAgent instance.

    Note:
        MCP plugins are NOT added here because they cannot be deep copied.
        They are added after kernel cloning in the orchestration layer.
    """
    plugins = load_plugins_for_agent(agent_config.name, config)

    return RealtimeAgent(
        name=agent_config.name,
        description=agent_config.description,
        instructions=agent_config.instructions,
        plugins=plugins,
        voice=agent_config.voice,
    )


def create_agents(config: Config | None = None) -> dict[str, RealtimeAgent]:
    """Create all agents from configuration.

    Args:
        config: Configuration object. If None, loads from default config.yaml.

    Returns:
        Dictionary mapping agent names to RealtimeAgent instances.
    """
    if config is None:
        config = get_config()

    agents = {}

    for agent_config in config.agents:
        try:
            agent = create_agent_from_config(agent_config, config)
            agents[agent_config.name] = agent
            logger.info(f"Created agent: {agent_config.name}")
        except Exception as e:
            logger.error(f"Failed to create agent '{agent_config.name}': {e}")
            raise

    return agents


def create_handoffs(agents: dict[str, RealtimeAgent], config: Config | None = None) -> OrchestrationHandoffs:
    """Create handoff configuration from config.yaml.

    Args:
        agents: Dictionary of agent name to RealtimeAgent instances.
        config: Configuration object. If None, loads from default config.yaml.

    Returns:
        OrchestrationHandoffs configuration.
    """
    if config is None:
        config = get_config()

    handoffs = OrchestrationHandoffs()

    for handoff_config in config.handoffs:
        source_agent = agents.get(handoff_config.from_agent)
        target_agent = agents.get(handoff_config.to)

        if source_agent and target_agent:
            handoffs.add(source_agent, target_agent, handoff_config.description)
            logger.info(f"Created handoff: {handoff_config.from_agent} -> {handoff_config.to}")
        else:
            if not source_agent:
                logger.warning(f"Handoff source agent '{handoff_config.from_agent}' not found")
            if not target_agent:
                logger.warning(f"Handoff target agent '{handoff_config.to}' not found")

    return handoffs
