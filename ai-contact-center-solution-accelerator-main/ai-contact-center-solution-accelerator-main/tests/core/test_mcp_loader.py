from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_contact_centre_solution_accelerator.config import AgentConfig, MCPServerConfig
from ai_contact_centre_solution_accelerator.core import mcp_loader
from ai_contact_centre_solution_accelerator.core.mcp_loader import (
    get_mcp_plugins_for_agent,
    start_mcp_plugins,
    stop_mcp_plugins,
)


@pytest.fixture(autouse=True)
def reset_mcp_plugins():
    mcp_loader._mcp_plugins.clear()
    yield
    mcp_loader._mcp_plugins.clear()


class TestStartMCPPlugins:
    async def test_start_http_plugin(self):
        mock_config = MagicMock()
        mock_config.mcp_servers = [
            MCPServerConfig(name="crm", transport="http", url="https://crm.example.com/mcp"),
        ]

        mock_plugin_instance = MagicMock()
        mock_plugin_instance.__aenter__ = AsyncMock(return_value=mock_plugin_instance)
        mock_plugin_instance.name = "crm"
        mock_plugin_instance.description = "CRM plugin"

        mock_kernel_plugin = MagicMock()
        mock_kernel_plugin.name = "crm"

        with (
            patch(
                "ai_contact_centre_solution_accelerator.core.mcp_loader.MCPStreamableHttpPlugin",
                return_value=mock_plugin_instance,
            ) as mock_cls,
            patch(
                "ai_contact_centre_solution_accelerator.core.mcp_loader.KernelPlugin.from_object",
                return_value=mock_kernel_plugin,
            ) as mock_from_object,
        ):
            await start_mcp_plugins(mock_config)

            mock_cls.assert_called_once_with(
                name="crm",
                url="https://crm.example.com/mcp",
                headers=None,
                description=None,
            )
            mock_plugin_instance.__aenter__.assert_awaited_once()
            mock_from_object.assert_called_once_with(
                plugin_name="crm",
                plugin_instance=mock_plugin_instance,
                description=None,
            )
            assert "crm" in mcp_loader._mcp_plugins
            assert mcp_loader._mcp_plugins["crm"] == mock_kernel_plugin

    async def test_start_stdio_plugin(self):
        mock_config = MagicMock()
        mock_config.mcp_servers = [
            MCPServerConfig(name="kb", transport="stdio", command="npx", args=["-y", "server"], env={"KEY": "val"}),
        ]

        mock_plugin_instance = MagicMock()
        mock_plugin_instance.__aenter__ = AsyncMock(return_value=mock_plugin_instance)
        mock_plugin_instance.name = "kb"
        mock_plugin_instance.description = "KB plugin"

        mock_kernel_plugin = MagicMock()
        mock_kernel_plugin.name = "kb"

        with (
            patch(
                "ai_contact_centre_solution_accelerator.core.mcp_loader.MCPStdioPlugin",
                return_value=mock_plugin_instance,
            ) as mock_cls,
            patch(
                "ai_contact_centre_solution_accelerator.core.mcp_loader.KernelPlugin.from_object",
                return_value=mock_kernel_plugin,
            ) as mock_from_object,
        ):
            await start_mcp_plugins(mock_config)

            mock_cls.assert_called_once_with(
                name="kb",
                command="npx",
                args=["-y", "server"],
                env={"KEY": "val"},
                description=None,
            )
            mock_plugin_instance.__aenter__.assert_awaited_once()
            mock_from_object.assert_called_once_with(
                plugin_name="kb",
                plugin_instance=mock_plugin_instance,
                description=None,
            )
            assert "kb" in mcp_loader._mcp_plugins
            assert mcp_loader._mcp_plugins["kb"] == mock_kernel_plugin

    async def test_skips_disabled_server(self):
        mock_config = MagicMock()
        mock_config.mcp_servers = [
            MCPServerConfig(name="disabled", transport="http", url="https://example.com", enabled=False),
        ]

        await start_mcp_plugins(mock_config)
        assert len(mcp_loader._mcp_plugins) == 0

    async def test_continues_on_failure(self):
        mock_config = MagicMock()
        mock_config.mcp_servers = [
            MCPServerConfig(name="bad", transport="http", url="https://bad.example.com"),
            MCPServerConfig(name="good", transport="http", url="https://good.example.com"),
        ]

        mock_bad = MagicMock()
        mock_bad.__aenter__ = AsyncMock(side_effect=Exception("connection failed"))

        mock_good = MagicMock()
        mock_good.__aenter__ = AsyncMock(return_value=mock_good)
        mock_good.name = "good"
        mock_good.description = "Good plugin"

        mock_kernel_plugin = MagicMock()
        mock_kernel_plugin.name = "good"

        call_count = 0

        def side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_bad
            return mock_good

        with (
            patch(
                "ai_contact_centre_solution_accelerator.core.mcp_loader.MCPStreamableHttpPlugin",
                side_effect=side_effect,
            ),
            patch(
                "ai_contact_centre_solution_accelerator.core.mcp_loader.KernelPlugin.from_object",
                return_value=mock_kernel_plugin,
            ),
        ):
            await start_mcp_plugins(mock_config)

        assert "bad" not in mcp_loader._mcp_plugins
        assert "good" in mcp_loader._mcp_plugins
        assert mcp_loader._mcp_plugins["good"] == mock_kernel_plugin


class TestStopMCPPlugins:
    async def test_stop_cleans_up(self):
        mock_plugin = MagicMock()
        mock_plugin.__aexit__ = AsyncMock()
        mcp_loader._mcp_plugins["test"] = mock_plugin

        await stop_mcp_plugins()

        mock_plugin.__aexit__.assert_awaited_once_with(None, None, None)
        assert len(mcp_loader._mcp_plugins) == 0


class TestGetMCPPluginsForAgent:
    def test_returns_plugins_for_agent(self):
        mock_crm = MagicMock()
        mock_kb = MagicMock()
        mcp_loader._mcp_plugins["crm"] = mock_crm
        mcp_loader._mcp_plugins["kb"] = mock_kb

        mock_config = MagicMock()
        mock_config.get_agent_by_name.return_value = AgentConfig(
            name="billing",
            description="Billing",
            instructions="Handle billing",
            mcp_servers=["crm"],
        )

        result = get_mcp_plugins_for_agent("billing", mock_config)
        assert result == [mock_crm]

    def test_returns_empty_for_agent_without_servers(self):
        mock_config = MagicMock()
        mock_config.get_agent_by_name.return_value = AgentConfig(
            name="test",
            description="Test",
            instructions="Test",
        )

        result = get_mcp_plugins_for_agent("test", mock_config)
        assert result == []

    def test_returns_empty_for_unknown_agent(self):
        mock_config = MagicMock()
        mock_config.get_agent_by_name.return_value = None

        result = get_mcp_plugins_for_agent("unknown", mock_config)
        assert result == []
