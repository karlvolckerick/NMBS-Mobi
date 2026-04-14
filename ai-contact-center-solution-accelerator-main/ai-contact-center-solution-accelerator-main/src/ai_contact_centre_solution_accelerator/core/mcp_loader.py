import logging

from semantic_kernel.connectors.mcp import MCPStdioPlugin, MCPStreamableHttpPlugin
from semantic_kernel.functions import KernelPlugin

from ai_contact_centre_solution_accelerator.config import Config

logger = logging.getLogger(__name__)

_mcp_plugins: dict[str, KernelPlugin] = {}


async def start_mcp_plugins(config: Config) -> None:
    """Start all enabled MCP plugins. Called at app startup."""
    for server in config.mcp_servers:
        if not server.enabled:
            continue

        try:
            if server.transport == "http":
                headers = None
                if server.headers:
                    headers = {k: v.get_secret_value() for k, v in server.headers.items()}

                mcp_plugin = MCPStreamableHttpPlugin(
                    name=server.name,
                    url=server.url,
                    headers=headers,
                    description=server.description or None,
                )
            else:
                env = None
                if server.env:
                    env = {k: v.get_secret_value() for k, v in server.env.items()}

                mcp_plugin = MCPStdioPlugin(
                    name=server.name,
                    command=server.command,
                    args=server.args,
                    env=env,
                    description=server.description or None,
                )

            await mcp_plugin.__aenter__()

            # Convert MCP plugin to KernelPlugin to ensure proper function naming
            # MCP plugins create functions with @kernel_function(name="tool_name") which
            # doesn't include the plugin prefix. Converting via from_object ensures
            # functions get the proper "plugin-function" naming format.
            kernel_plugin = KernelPlugin.from_object(
                plugin_name=server.name,
                plugin_instance=mcp_plugin,
                description=server.description or None,
            )

            _mcp_plugins[server.name] = kernel_plugin
            logger.info(f"Started MCP plugin '{server.name}' ({server.transport})")
        except Exception:
            logger.exception(f"Failed to start MCP plugin '{server.name}'")


async def stop_mcp_plugins() -> None:
    """Stop all MCP plugins. Called at app shutdown."""
    for name, plugin in _mcp_plugins.items():
        try:
            await plugin.__aexit__(None, None, None)
            logger.info(f"Stopped MCP plugin '{name}'")
        except Exception:
            logger.exception(f"Failed to stop MCP plugin '{name}'")
    _mcp_plugins.clear()


def get_mcp_plugins_for_agent(agent_name: str, config: Config) -> list[KernelPlugin]:
    """Get MCP plugins assigned to an agent.

    Args:
        agent_name: The agent name to look up.
        config: Application configuration.

    Returns:
        List of KernelPlugin instances for the agent's configured MCP servers.
    """
    agent_config = config.get_agent_by_name(agent_name)
    if not agent_config:
        logger.warning(f"No agent config found for '{agent_name}'")
        return []

    requested = agent_config.mcp_servers
    available = list(_mcp_plugins.keys())
    plugins = [_mcp_plugins[name] for name in requested if name in _mcp_plugins]

    logger.info(f"Agent '{agent_name}' MCP: requested={requested}, available={available}, matched={len(plugins)}")
    return plugins
