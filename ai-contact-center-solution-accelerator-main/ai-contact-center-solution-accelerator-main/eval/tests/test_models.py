from eval.models import (
    FunctionCallExpectation,
    ScenarioResult,
)


class TestFunctionCallExpectation:
    def test_matches_same(self):
        a = FunctionCallExpectation(plugin="BillingPlugin", function_name="get_balance")
        b = FunctionCallExpectation(plugin="BillingPlugin", function_name="get_balance")
        assert a.matches(b)

    def test_no_match_different_function(self):
        a = FunctionCallExpectation(plugin="BillingPlugin", function_name="get_balance")
        b = FunctionCallExpectation(plugin="BillingPlugin", function_name="process_payment")
        assert not a.matches(b)

    def test_no_match_different_plugin(self):
        a = FunctionCallExpectation(plugin="BillingPlugin", function_name="get_balance")
        b = FunctionCallExpectation(plugin="SupportPlugin", function_name="get_balance")
        assert not a.matches(b)


class TestScenarioResult:
    def test_defaults(self):
        result = ScenarioResult(scenario_name="test")
        assert result.transcript == []
        assert result.function_calls == []
        assert result.function_results == []
        assert result.agent_switches == []
        assert result.final_agent is None
        assert result.turns == 0
        assert result.error == ""
