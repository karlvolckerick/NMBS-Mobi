"""
RealtimeAgent - A lightweight agent for realtime voice orchestration.

RealtimeAgent is a configuration container that holds agent-specific settings
for use in realtime conversations. Unlike traditional agents, RealtimeAgents
do not own their own session - instead, multiple RealtimeAgents share a single
realtime session managed by the orchestration.
"""

import uuid
from typing import Any

from pydantic import Field
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.naming import generate_random_ascii_name
from semantic_kernel.utils.validation import AGENT_NAME_REGEX


class RealtimeAgent(KernelBaseModel):
    """A realtime agent that participates in multi-agent voice orchestration.

    Attributes:
        id: The unique identifier of the agent.
        name: The name of the agent (used in handoff function names).
        description: A description of the agent (used in handoff function descriptions).
        instructions: The system instructions for this agent.
        kernel: The kernel instance containing plugins/functions for this agent.
        function_choice_behavior: How the agent should handle function calling.
        voice: The voice to use for this agent (optional, for voice switching).
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(default_factory=lambda: f"agent_{generate_random_ascii_name()}", pattern=AGENT_NAME_REGEX)
    description: str | None = None
    instructions: str | None = None
    kernel: Kernel = Field(default_factory=Kernel)
    function_choice_behavior: FunctionChoiceBehavior | None = Field(
        default_factory=lambda: FunctionChoiceBehavior.Auto()
    )
    voice: str | None = None

    def __init__(
        self,
        *,
        id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        kernel: Kernel | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        voice: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a RealtimeAgent.

        Args:
            id: The unique identifier of the agent. If not provided, a UUID will be generated.
            name: The name of the agent. If not provided, a random name will be generated.
            description: A description of the agent, used in handoff function descriptions.
            instructions: The system instructions for this agent.
            kernel: The kernel instance containing plugins/functions. If not provided,
                a new Kernel will be created.
            plugins: Plugins to add to the kernel. Can be a list of plugin objects or
                a dict mapping names to plugins.
            function_choice_behavior: How the agent should handle function calling.
                Defaults to FunctionChoiceBehavior.Auto().
            voice: The voice to use for this agent (e.g., "alloy", "echo", "shimmer").
            **kwargs: Additional keyword arguments.
        """
        args: dict[str, Any] = {}

        if id is not None:
            args["id"] = id
        if name is not None:
            args["name"] = name
        if description is not None:
            args["description"] = description
        if instructions is not None:
            args["instructions"] = instructions
        if function_choice_behavior is not None:
            args["function_choice_behavior"] = function_choice_behavior
        if voice is not None:
            args["voice"] = voice

        # Handle kernel and plugins
        if kernel is not None:
            args["kernel"] = kernel
        else:
            args["kernel"] = Kernel()

        if plugins is not None:
            kernel_instance = args["kernel"]
            if isinstance(plugins, list):
                for plugin in plugins:
                    if isinstance(plugin, KernelPlugin):
                        kernel_instance.add_plugin(plugin)
                    else:
                        kernel_instance.add_plugin(plugin)
            elif isinstance(plugins, dict):
                for plugin_name, plugin in plugins.items():
                    if isinstance(plugin, KernelPlugin):
                        kernel_instance.add_plugin(plugin)
                    else:
                        kernel_instance.add_plugin(plugin, plugin_name=plugin_name)

        super().__init__(**args, **kwargs)

    def __str__(self) -> str:
        """Return a string representation of the agent."""
        return f"RealtimeAgent(name={self.name}, description={self.description})"

    def __repr__(self) -> str:
        """Return a detailed string representation of the agent."""
        instructions_preview = self.instructions[:50] if self.instructions else None
        return (
            f"RealtimeAgent(id={self.id}, name={self.name}, "
            f"description={self.description}, instructions={instructions_preview}...)"
        )
