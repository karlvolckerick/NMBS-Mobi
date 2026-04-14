"""
Example plugin module demonstrating how to create plugins for agents.

This file serves as a template for creating new plugin modules.
Plugins are classes with methods decorated with @kernel_function.

Usage:
1. Create a new Python file in src/tools/ (e.g., billing_tools.py)
2. Define a class with methods decorated with @kernel_function
3. Add the plugin to config.yaml under the 'plugins' section
4. Assign the plugin to agents in config.yaml

Example config.yaml entry:
    plugins:
      - name: "my_plugin"
        module: "my_tools"
        class_name: "MyPlugin"
        description: "My custom plugin"

    agents:
      - name: "my_agent"
        plugins:
          - "my_plugin"
"""

import datetime
from random import randint

from semantic_kernel.functions.kernel_function_decorator import kernel_function


class ReceptionistPlugin:
    """Plugin with functions available to the receptionist agent."""

    @kernel_function
    def get_current_time(self) -> str:
        """Get the current time."""
        return f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}."

    @kernel_function
    def get_office_hours(self) -> str:
        """Get the office hours."""
        return "Our office hours are Monday through Friday, 9 AM to 5 PM Eastern Time."


class BillingPlugin:
    """Plugin with functions available to the billing agent."""

    @kernel_function
    def get_account_balance(self, account_id: str = "default") -> str:
        """Get the account balance for a customer."""
        # Simulated balance
        balance = randint(50, 500)  # nosec
        return f"The current balance for account {account_id} is ${balance:.2f}."

    @kernel_function
    def get_payment_methods(self) -> str:
        """Get available payment methods."""
        return "We accept credit cards (Visa, MasterCard, American Express), bank transfers, and PayPal."

    @kernel_function
    def process_payment(self, amount: float, method: str = "credit card") -> str:
        """Process a payment."""
        return f"Payment of ${amount:.2f} via {method} has been processed successfully."


class SupportPlugin:
    """Plugin with functions available to the support agent."""

    @kernel_function
    def check_system_status(self) -> str:
        """Check the current system status."""
        statuses = ["All systems operational", "Minor delays in some regions", "Maintenance scheduled"]
        return statuses[randint(0, len(statuses) - 1)]  # nosec

    @kernel_function
    def create_support_ticket(self, issue_description: str) -> str:
        """Create a support ticket for the customer."""
        ticket_id = f"TKT-{randint(10000, 99999)}"  # nosec
        return f"Support ticket {ticket_id} has been created for: {issue_description}"

    @kernel_function
    def get_troubleshooting_steps(self, issue_type: str) -> str:
        """Get troubleshooting steps for common issues."""
        steps = {
            "connectivity": "1. Check your internet connection. 2. Restart your router. 3. Clear browser cache.",
            "login": "1. Verify your username and password. 2. Check caps lock. 3. Try password reset.",
            "performance": "1. Close unused applications. 2. Clear temporary files. 3. Restart your device.",
        }
        return steps.get(issue_type.lower(), "Please describe your issue in more detail.")
