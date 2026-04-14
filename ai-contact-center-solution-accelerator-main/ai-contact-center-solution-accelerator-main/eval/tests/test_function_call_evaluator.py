from eval.evaluators.function_call import FunctionCallEvaluator


class TestFunctionCallEvaluator:
    def test_perfect_score(self):
        result = FunctionCallEvaluator()(
            function_calls=[{"agent": "billing", "plugin": "BillingPlugin", "function": "get_balance"}],
            expected_function_calls=[{"plugin": "BillingPlugin", "function_name": "get_balance"}],
            unexpected_function_calls=[],
        )
        assert result["function_call_precision"] == 1.0
        assert result["function_call_recall"] == 1.0
        assert result["function_call_f1"] == 1.0
        assert result["function_call_faults"] == 0

    def test_no_calls_when_expected(self):
        result = FunctionCallEvaluator()(
            function_calls=[],
            expected_function_calls=[{"plugin": "BillingPlugin", "function_name": "get_balance"}],
            unexpected_function_calls=[],
        )
        assert result["function_call_precision"] == 0
        assert result["function_call_recall"] == 0
        assert result["function_call_f1"] == 0

    def test_unexpected_call_counted_as_fault(self):
        result = FunctionCallEvaluator()(
            function_calls=[
                {"agent": "billing", "plugin": "BillingPlugin", "function": "get_balance"},
                {"agent": "billing", "plugin": "BillingPlugin", "function": "process_payment"},
            ],
            expected_function_calls=[{"plugin": "BillingPlugin", "function_name": "get_balance"}],
            unexpected_function_calls=[{"plugin": "BillingPlugin", "function_name": "process_payment"}],
        )
        assert result["function_call_recall"] == 1.0
        assert result["function_call_precision"] == 0.5
        assert result["function_call_faults"] == 1

    def test_partial_recall(self):
        result = FunctionCallEvaluator()(
            function_calls=[{"agent": "billing", "plugin": "BillingPlugin", "function": "get_balance"}],
            expected_function_calls=[
                {"plugin": "BillingPlugin", "function_name": "get_balance"},
                {"plugin": "BillingPlugin", "function_name": "get_payment_methods"},
            ],
            unexpected_function_calls=[],
        )
        assert result["function_call_precision"] == 1.0
        assert result["function_call_recall"] == 0.5

    def test_none_function_calls_returns_empty(self):
        result = FunctionCallEvaluator()(
            function_calls=None,
            expected_function_calls=[{"plugin": "P", "function_name": "f"}],
            unexpected_function_calls=[],
        )
        assert result["function_call_precision"] is None
        assert result["function_call_recall"] is None

    def test_no_expected_no_actual(self):
        result = FunctionCallEvaluator()(
            function_calls=[],
            expected_function_calls=[],
            unexpected_function_calls=[],
        )
        assert result["function_call_precision"] == 0
        assert result["function_call_recall"] == 0
        assert result["function_call_faults"] == 0
