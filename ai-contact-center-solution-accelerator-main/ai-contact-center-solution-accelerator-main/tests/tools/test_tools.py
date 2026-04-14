import pytest
import yaml

from ai_contact_centre_solution_accelerator.config import load_config
from ai_contact_centre_solution_accelerator.tools.example_tools import BillingPlugin, ReceptionistPlugin, SupportPlugin
from ai_contact_centre_solution_accelerator.tools.loader import (
    ToolRegistry,
    get_all_plugin_modules,
    load_plugin_class,
    load_plugins_for_agent,
    validate_plugin_modules,
)


class TestToolRegistry:
    def test_registry_clear(self):
        ToolRegistry._instances["test"] = "value"
        ToolRegistry._classes["test"] = str

        ToolRegistry.clear()

        assert len(ToolRegistry._instances) == 0
        assert len(ToolRegistry._classes) == 0

    def test_register_class(self):
        ToolRegistry.clear()

        class TestClass:
            pass

        ToolRegistry.register_class("test", TestClass)

        assert "test" in ToolRegistry._classes
        assert ToolRegistry._classes["test"] is TestClass

    def test_get_instance_creates_new(self):
        ToolRegistry.clear()

        class TestClass:
            pass

        ToolRegistry.register_class("test", TestClass)
        instance = ToolRegistry.get_instance("test")

        assert instance is not None
        assert isinstance(instance, TestClass)

    def test_get_instance_returns_cached(self):
        ToolRegistry.clear()

        class TestClass:
            pass

        ToolRegistry.register_class("test", TestClass)
        instance1 = ToolRegistry.get_instance("test")
        instance2 = ToolRegistry.get_instance("test")

        assert instance1 is instance2

    def test_get_instance_not_registered(self):
        ToolRegistry.clear()

        instance = ToolRegistry.get_instance("nonexistent")

        assert instance is None


class TestLoadPluginClass:
    def test_load_receptionist_plugin(self):
        instance = load_plugin_class("example_tools", "ReceptionistPlugin")

        assert instance is not None
        assert instance.__class__.__name__ == "ReceptionistPlugin"

    def test_load_billing_plugin(self):
        instance = load_plugin_class("example_tools", "BillingPlugin")

        assert instance is not None
        assert instance.__class__.__name__ == "BillingPlugin"

    def test_load_support_plugin(self):
        instance = load_plugin_class("example_tools", "SupportPlugin")

        assert instance is not None
        assert instance.__class__.__name__ == "SupportPlugin"

    def test_load_nonexistent_module(self):
        with pytest.raises(ImportError):
            load_plugin_class("nonexistent_module", "SomeClass")

    def test_load_nonexistent_class(self):
        with pytest.raises(AttributeError):
            load_plugin_class("example_tools", "NonexistentClass")


class TestLoadPluginsForAgent:
    def test_load_plugins_no_plugins_configured(self, config_with_agents):
        config = load_config(config_with_agents)

        plugins = load_plugins_for_agent("receptionist", config)

        assert len(plugins) == 0

    def test_load_plugins_with_plugins_configured(self, config_with_plugins):
        config = load_config(config_with_plugins)

        plugins = load_plugins_for_agent("receptionist", config)

        assert len(plugins) == 1
        assert plugins[0].__class__.__name__ == "ReceptionistPlugin"

    def test_load_plugins_nonexistent_agent(self, config_with_agents):
        config = load_config(config_with_agents)

        plugins = load_plugins_for_agent("nonexistent", config)

        assert len(plugins) == 0


class TestGetAllPluginModules:
    def test_get_modules_empty(self, minimal_config):
        config = load_config(minimal_config)

        modules = get_all_plugin_modules(config)

        assert len(modules) == 0

    def test_get_modules_with_plugins(self, config_with_plugins):
        config = load_config(config_with_plugins)

        modules = get_all_plugin_modules(config)

        assert "example_tools" in modules


class TestValidatePluginModules:
    def test_validate_valid_plugins(self, config_with_plugins):
        config = load_config(config_with_plugins)

        errors = validate_plugin_modules(config)

        assert len(errors) == 0

    def test_validate_invalid_module(self, test_config_dir):
        config_data = {
            "app": {"name": "Test", "description": "Test", "version": "1.0.0"},
            "azure_openai": {"endpoint": "https://test.openai.azure.com/", "deployment": "gpt-4o-realtime"},
            "server": {"host": "0.0.0.0", "port": 8000, "log_level": "INFO"},
            "voice": {"default": "alloy"},
            "turn_detection": {
                "type": "server_vad",
                "silence_duration_ms": 800,
                "threshold": 0.8,
                "create_response": True,
            },
            "agents": [{"name": "test_agent", "description": "Test agent", "instructions": "Test instructions"}],
            "handoffs": [],
            "plugins": [
                {
                    "name": "test_plugin",
                    "module": "nonexistent_module",
                    "class_name": "TestClass",
                    "description": "Test",
                },
            ],
            "orchestration": {"silent_handoffs": True},
        }

        config_path = test_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(config_path)
        errors = validate_plugin_modules(config)

        assert len(errors) > 0
        assert "nonexistent_module" in errors[0]

    def test_validate_invalid_class(self, test_config_dir):
        config_data = {
            "app": {"name": "Test", "description": "Test", "version": "1.0.0"},
            "azure_openai": {"endpoint": "https://test.openai.azure.com/", "deployment": "gpt-4o-realtime"},
            "server": {"host": "0.0.0.0", "port": 8000, "log_level": "INFO"},
            "voice": {"default": "alloy"},
            "turn_detection": {
                "type": "server_vad",
                "silence_duration_ms": 800,
                "threshold": 0.8,
                "create_response": True,
            },
            "agents": [{"name": "test_agent", "description": "Test agent", "instructions": "Test instructions"}],
            "handoffs": [],
            "plugins": [
                {
                    "name": "test_plugin",
                    "module": "example_tools",
                    "class_name": "NonexistentClass",
                    "description": "Test",
                },
            ],
            "orchestration": {"silent_handoffs": True},
        }

        config_path = test_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(config_path)
        errors = validate_plugin_modules(config)

        assert len(errors) > 0
        assert "NonexistentClass" in errors[0]


class TestExamplePlugins:
    def test_receptionist_get_current_time(self):
        plugin = ReceptionistPlugin()
        result = plugin.get_current_time()

        assert "current time" in result.lower()

    def test_receptionist_get_office_hours(self):
        plugin = ReceptionistPlugin()
        result = plugin.get_office_hours()

        assert "office hours" in result.lower() or "9 AM" in result

    def test_billing_get_account_balance(self):
        plugin = BillingPlugin()
        result = plugin.get_account_balance("ACC001")

        assert "balance" in result.lower() or "$" in result

    def test_billing_get_payment_methods(self):
        plugin = BillingPlugin()
        result = plugin.get_payment_methods()

        assert "credit" in result.lower() or "payment" in result.lower()

    def test_billing_process_payment(self):
        plugin = BillingPlugin()
        result = plugin.process_payment(100.00, "credit card")

        assert "processed" in result.lower()

    def test_support_check_system_status(self):
        plugin = SupportPlugin()
        result = plugin.check_system_status()

        assert result is not None

    def test_support_create_ticket(self):
        plugin = SupportPlugin()
        result = plugin.create_support_ticket("Test issue")

        assert "TKT-" in result

    def test_support_get_troubleshooting_steps(self):
        plugin = SupportPlugin()
        result = plugin.get_troubleshooting_steps("connectivity")

        assert "internet" in result.lower() or "router" in result.lower()
