"""
Plugin loader for dynamically loading plugins from config.yaml.

Plugins are Python classes in src/tools/ that contain methods
decorated with @kernel_function. This module provides functionality to
load and instantiate plugin classes based on configuration.

Each plugin is a class that groups related functions together,
and agents can be assigned one or more plugins.
"""

import importlib
import inspect
import logging
from typing import Any

from ai_contact_centre_solution_accelerator.config import Config

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for tool classes and instances."""

    _instances: dict[str, Any] = {}
    _classes: dict[str, type] = {}

    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools."""
        cls._instances.clear()
        cls._classes.clear()

    @classmethod
    def register_class(cls, name: str, tool_class: type) -> None:
        """Register a tool class."""
        cls._classes[name] = tool_class

    @classmethod
    def get_instance(cls, name: str) -> Any | None:
        """Get or create a tool instance by name."""
        if name not in cls._instances:
            if name in cls._classes:
                cls._instances[name] = cls._classes[name]()
            else:
                return None
        return cls._instances[name]


def _find_tool_classes(module: Any) -> list[tuple[str, type]]:
    """Find all classes in a module that have kernel_function decorated methods.

    Args:
        module: The Python module to search.

    Returns:
        List of (name, class) tuples for classes with kernel_function methods.
    """
    tool_classes = []

    for name, obj in inspect.getmembers(module, inspect.isclass):
        # Skip imported classes (only include classes defined in this module)
        if obj.__module__ != module.__name__:
            continue

        # Check if any method has the kernel_function decorator
        has_kernel_functions = False
        for method_name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
            if hasattr(method, "__kernel_function__"):
                has_kernel_functions = True
                break

        if has_kernel_functions:
            tool_classes.append((name, obj))

    return tool_classes


def load_tool_module(module_name: str) -> list[Any]:
    """Load a tool module and return instances of all tool classes.

    Args:
        module_name: The module name (without .py extension) in src/tools/.

    Returns:
        List of tool class instances from the module.

    Raises:
        ImportError: If the module cannot be imported.
    """
    full_module_name = f"ai_contact_centre_solution_accelerator.tools.{module_name}"

    try:
        module = importlib.import_module(full_module_name)
    except ImportError as e:
        logger.error(f"Failed to import tool module '{full_module_name}': {e}")
        raise

    tool_classes = _find_tool_classes(module)
    instances = []

    for class_name, tool_class in tool_classes:
        try:
            instance = tool_class()
            instances.append(instance)
            ToolRegistry.register_class(f"{module_name}.{class_name}", tool_class)
            logger.debug(f"Loaded tool class: {class_name} from {module_name}")
        except Exception as e:
            logger.error(f"Failed to instantiate tool class '{class_name}': {e}")
            raise

    return instances


def load_plugin_class(module_name: str, class_name: str) -> Any:
    """Load a specific plugin class from a module and return an instance.

    Args:
        module_name: The module name (without .py extension) in src/tools/.
        class_name: The class name within the module.

    Returns:
        Instance of the plugin class.

    Raises:
        ImportError: If the module cannot be imported.
        AttributeError: If the class is not found in the module.
    """
    full_module_name = f"ai_contact_centre_solution_accelerator.tools.{module_name}"

    try:
        module = importlib.import_module(full_module_name)
    except ImportError as e:
        logger.error(f"Failed to import tool module '{full_module_name}': {e}")
        raise

    if not hasattr(module, class_name):
        raise AttributeError(f"Class '{class_name}' not found in module '{full_module_name}'")

    plugin_class = getattr(module, class_name)
    instance = plugin_class()
    ToolRegistry.register_class(f"{module_name}.{class_name}", plugin_class)
    logger.debug(f"Loaded plugin class: {class_name} from {module_name}")
    return instance


def load_plugins_for_agent(agent_name: str, config: Config) -> list[Any]:
    """Load all plugins assigned to an agent from config.yaml.

    Args:
        agent_name: The name of the agent.
        config: The configuration object.

    Returns:
        List of plugin instances for the agent.
    """
    plugin_configs = config.get_plugins_for_agent(agent_name)

    if not plugin_configs:
        logger.debug(f"No plugins configured for agent '{agent_name}'")
        return []

    plugins = []

    for plugin_config in plugin_configs:
        try:
            instance = load_plugin_class(plugin_config.module, plugin_config.class_name)
            plugins.append(instance)
        except (ImportError, AttributeError) as e:
            logger.warning(f"Skipping plugin '{plugin_config.name}' - {e}")
            continue

    logger.info(f"Loaded {len(plugins)} plugin(s) for agent '{agent_name}'")
    return plugins


def get_all_plugin_modules(config: Config) -> set[str]:
    """Get all unique plugin module names from configuration.

    Args:
        config: The configuration object.

    Returns:
        Set of module names.
    """
    return {plugin.module for plugin in config.plugins}


def validate_plugin_modules(config: Config) -> list[str]:
    """Validate that all configured plugins can be imported.

    Args:
        config: The configuration object.

    Returns:
        List of error messages for plugins that failed to load.
    """
    errors = []

    for plugin_config in config.plugins:
        try:
            load_plugin_class(plugin_config.module, plugin_config.class_name)
        except ImportError as e:
            errors.append(f"Plugin module '{plugin_config.module}' failed to import: {e}")
        except AttributeError as e:
            errors.append(f"Plugin class '{plugin_config.class_name}' not found: {e}")
        except Exception as e:
            errors.append(f"Plugin '{plugin_config.name}' failed to load: {e}")

    return errors
