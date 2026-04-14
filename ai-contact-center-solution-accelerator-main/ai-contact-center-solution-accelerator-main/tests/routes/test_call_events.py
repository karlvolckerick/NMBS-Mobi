import json
from unittest.mock import AsyncMock, MagicMock

from ai_contact_centre_solution_accelerator.routes.call import (
    send_function_call,
    send_function_result,
)


class TestSendFunctionCall:
    async def test_sends_function_call_event(self):
        websocket = MagicMock()
        websocket.send_text = AsyncMock()

        await send_function_call(
            websocket,
            agent_name="billing",
            plugin_name="BillingPlugin",
            function_name="get_account_balance",
            arguments='{"account_id": "ACC001"}',
        )

        websocket.send_text.assert_called_once()
        sent = json.loads(websocket.send_text.call_args[0][0])
        assert sent["kind"] == "FunctionCall"
        assert sent["data"]["agent"] == "billing"
        assert sent["data"]["plugin"] == "BillingPlugin"
        assert sent["data"]["function"] == "get_account_balance"
        assert sent["data"]["arguments"] == '{"account_id": "ACC001"}'

    async def test_excludes_transfer_functions(self):
        websocket = MagicMock()
        websocket.send_text = AsyncMock()

        await send_function_call(
            websocket,
            agent_name="receptionist",
            plugin_name="handoffs",
            function_name="transfer_to_billing",
            arguments="",
        )

        websocket.send_text.assert_not_called()

    async def test_handles_send_failure(self):
        websocket = MagicMock()
        websocket.send_text = AsyncMock(side_effect=Exception("connection closed"))

        await send_function_call(
            websocket,
            agent_name="billing",
            plugin_name="BillingPlugin",
            function_name="get_balance",
            arguments="",
        )


class TestSendFunctionResult:
    async def test_sends_function_result_event(self):
        websocket = MagicMock()
        websocket.send_text = AsyncMock()

        await send_function_result(
            websocket,
            agent_name="billing",
            plugin_name="BillingPlugin",
            function_name="get_account_balance",
            result="Balance: $150.00",
        )

        websocket.send_text.assert_called_once()
        sent = json.loads(websocket.send_text.call_args[0][0])
        assert sent["kind"] == "FunctionResult"
        assert sent["data"]["agent"] == "billing"
        assert sent["data"]["plugin"] == "BillingPlugin"
        assert sent["data"]["function"] == "get_account_balance"
        assert sent["data"]["result"] == "Balance: $150.00"

    async def test_excludes_transfer_functions(self):
        websocket = MagicMock()
        websocket.send_text = AsyncMock()

        await send_function_result(
            websocket,
            agent_name="receptionist",
            plugin_name="handoffs",
            function_name="transfer_to_billing",
            result="OK",
        )

        websocket.send_text.assert_not_called()
