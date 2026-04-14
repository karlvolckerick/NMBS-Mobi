"""Tests for MCP plugin integration with agents."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_contact_centre_solution_accelerator.agents.agent_factory import create_handoffs
from ai_contact_centre_solution_accelerator.agents.realtime_agent import RealtimeAgent
from ai_contact_centre_solution_accelerator.config import AgentConfig, Config, MCPServerConfig
from ai_contact_centre_solution_accelerator.core.mcp_loader import get_mcp_plugins_for_agent, start_mcp_plugins
from ai_contact_centre_solution_accelerator.core.orchestration import RealtimeHandoffOrchestration


@pytest.fixture
def config_with_mcp():
    """Create a config with MCP servers."""
    return Config(
        azure_openai={
            "endpoint": "https://test.openai.azure.com/",
            "deployment": "gpt-4o-realtime",
            "api_version": "2024-10-01-preview",
        },
        agents=[
            AgentConfig(
                name="agent1",
                description="Test agent",
                instructions="Test instructions",
                mcp_servers=["test_server"],
            ),
            AgentConfig(
                name="agent2",
                description="Agent without MCP",
                instructions="Test instructions",
                mcp_servers=[],
            ),
        ],
        handoffs=[
            {
                "from": "agent1",
                "to": "agent2",
                "description": "Test handoff",
            },
        ],
        mcp_servers=[
            MCPServerConfig(
                name="test_server",
                transport="stdio",
                command="test-command",
                args=[],
                enabled=True,
            ),
        ],
    )


class TestMCPIntegration:
    async def test_mcp_plugins_added_to_agent_kernels(self, config_with_mcp):
        """Test that MCP plugins are added to agent kernels in orchestration."""
        # Mock the MCP plugin
        mock_plugin = MagicMock()
        mock_plugin.__aenter__ = AsyncMock(return_value=mock_plugin)
        mock_plugin.__aexit__ = AsyncMock()
        mock_plugin.name = "test_server"
        mock_plugin.description = "Test MCP server"

        with patch(
            "ai_contact_centre_solution_accelerator.core.mcp_loader.MCPStdioPlugin",
            return_value=mock_plugin,
        ):
            # Start MCP plugins
            await start_mcp_plugins(config_with_mcp)

            # Create agents
            agent1 = RealtimeAgent(
                name="agent1",
                description="Test agent",
                instructions="Test instructions",
            )
            agent2 = RealtimeAgent(
                name="agent2",
                description="Agent without MCP",
                instructions="Test instructions",
            )

            # Build handoffs from config
            agents_dict = {"agent1": agent1, "agent2": agent2}
            handoffs = create_handoffs(agents_dict, config_with_mcp)

            # Create mock realtime client
            mock_client = MagicMock()
            mock_client.update_session = AsyncMock()

            # Create orchestration
            with patch(
                "ai_contact_centre_solution_accelerator.core.orchestration.get_config", return_value=config_with_mcp
            ):
                orchestration = RealtimeHandoffOrchestration(
                    members=[agent1, agent2],
                    handoffs=handoffs,
                    realtime_client=mock_client,
                )

                # Check that agent1's kernel has the MCP plugin
                agent1_kernel = orchestration._agent_kernels.get("agent1")
                assert agent1_kernel is not None, "agent1 should have a kernel in _agent_kernels"

                # Get plugins from agent1's kernel
                agent1_plugins = list(agent1_kernel.plugins.values())
                assert any(p.name == "test_server" for p in agent1_plugins), "agent1 should have test_server plugin"

                # Check that agent2's kernel does NOT have the MCP plugin
                agent2_kernel = orchestration._agent_kernels.get("agent2")
                assert agent2_kernel is not None, "agent2 should have a kernel in _agent_kernels"

                agent2_plugins = list(agent2_kernel.plugins.values())
                assert not any(p.name == "test_server" for p in agent2_plugins), (
                    "agent2 should NOT have test_server plugin"
                )

    async def test_get_mcp_plugins_for_agent(self, config_with_mcp):
        """Test that get_mcp_plugins_for_agent returns correct plugins."""
        # Mock the MCP plugin
        mock_plugin = MagicMock()
        mock_plugin.__aenter__ = AsyncMock(return_value=mock_plugin)
        mock_plugin.__aexit__ = AsyncMock()
        mock_plugin.name = "test_server"
        mock_plugin.description = "Test MCP server"

        with patch(
            "ai_contact_centre_solution_accelerator.core.mcp_loader.MCPStdioPlugin",
            return_value=mock_plugin,
        ):
            # Start MCP plugins
            await start_mcp_plugins(config_with_mcp)

            # Get plugins for agent1 (should have test_server)
            agent1_plugins = get_mcp_plugins_for_agent("agent1", config_with_mcp)
            assert len(agent1_plugins) == 1
            assert agent1_plugins[0].name == "test_server"

            # Get plugins for agent2 (should have none)
            agent2_plugins = get_mcp_plugins_for_agent("agent2", config_with_mcp)
            assert len(agent2_plugins) == 0

    async def test_mcp_plugins_available_after_agent_switch(self, config_with_mcp):
        """Test that MCP plugins are available in the kernel after agent switch."""
        # Mock the MCP plugin
        mock_plugin = MagicMock()
        mock_plugin.__aenter__ = AsyncMock(return_value=mock_plugin)
        mock_plugin.__aexit__ = AsyncMock()
        mock_plugin.name = "test_server"
        mock_plugin.description = "Test MCP server"

        with patch(
            "ai_contact_centre_solution_accelerator.core.mcp_loader.MCPStdioPlugin",
            return_value=mock_plugin,
        ):
            # Start MCP plugins
            await start_mcp_plugins(config_with_mcp)

            # Create agents - need two agents for handoff
            agent1 = RealtimeAgent(
                name="agent1",
                description="Test agent",
                instructions="Test instructions",
            )
            agent2 = RealtimeAgent(
                name="agent2",
                description="Agent without MCP",
                instructions="Test instructions",
            )

            # Build handoffs from config
            agents_dict = {"agent1": agent1, "agent2": agent2}
            handoffs = create_handoffs(agents_dict, config_with_mcp)

            # Create mock realtime client
            mock_client = MagicMock()
            mock_client.update_session = AsyncMock()

            # Create orchestration
            with patch(
                "ai_contact_centre_solution_accelerator.core.orchestration.get_config", return_value=config_with_mcp
            ):
                orchestration = RealtimeHandoffOrchestration(
                    members=[agent1, agent2],
                    handoffs=handoffs,
                    realtime_client=mock_client,
                )

                # Switch to agent1
                await orchestration._switch_to_agent(agent1)

                # Verify update_session was called with a kernel that has the MCP plugin
                assert mock_client.update_session.called
                call_kwargs = mock_client.update_session.call_args.kwargs
                kernel_used = call_kwargs.get("kernel")

                assert kernel_used is not None
                plugins = list(kernel_used.plugins.values())
                assert any(p.name == "test_server" for p in plugins), (
                    "Kernel should have test_server plugin after switch"
                )
