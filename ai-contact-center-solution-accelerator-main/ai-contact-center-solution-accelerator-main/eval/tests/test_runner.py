import json
from io import StringIO
from unittest.mock import patch

import pytest

from eval.runner import TransportFactory, _safe_mean, load_scenarios, print_summary_table


class TestLoadScenarios:
    def test_load_jsonl(self, tmp_path):
        jsonl_path = tmp_path / "test.jsonl"
        scenarios = [
            {
                "scenario_name": "test1",
                "category": "billing",
                "instructions": "Check balance",
                "expected_function_calls": [],
                "unexpected_function_calls": [],
            },
            {
                "scenario_name": "test2",
                "category": "support",
                "instructions": "Create ticket",
                "expected_function_calls": [],
                "unexpected_function_calls": [],
            },
        ]
        with open(jsonl_path, "w") as f:
            for s in scenarios:
                f.write(json.dumps(s) + "\n")

        loaded = load_scenarios(jsonl_path)
        assert len(loaded) == 2
        assert loaded[0]["scenario_name"] == "test1"
        assert loaded[1]["category"] == "support"

    def test_load_nonexistent_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_scenarios(tmp_path / "missing.jsonl")


class TestSafeMean:
    def test_normal_values(self):
        assert _safe_mean([1.0, 2.0, 3.0]) == "2.00"

    def test_empty_list(self):
        assert _safe_mean([]) == "N/A"

    def test_all_none(self):
        assert _safe_mean([None, None, None]) == "N/A"

    def test_mixed_values_and_none(self):
        assert _safe_mean([1.0, None, 3.0, None]) == "2.00"

    def test_single_value(self):
        assert _safe_mean([4.5]) == "4.50"


class TestPrintSummaryTable:
    def test_prints_table_with_results(self):
        results = [
            {
                "inputs.category": "billing",
                "outputs.function_call.function_call_recall": 0.95,
                "outputs.function_call.function_call_precision": 1.0,
                "outputs.intent_resolution.intent_resolution": 4.2,
                "outputs.coherence.coherence": 4.5,
            },
            {
                "inputs.category": "billing",
                "outputs.function_call.function_call_recall": 1.0,
                "outputs.function_call.function_call_precision": 1.0,
                "outputs.intent_resolution.intent_resolution": 4.0,
                "outputs.coherence.coherence": 4.3,
            },
            {
                "inputs.category": "support",
                "outputs.function_call.function_call_recall": 0.88,
                "outputs.function_call.function_call_precision": 0.92,
                "outputs.intent_resolution.intent_resolution": 3.8,
                "outputs.coherence.coherence": 4.1,
            },
        ]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_summary_table(results)
            output = mock_stdout.getvalue()

        assert "Category" in output
        assert "billing" in output
        assert "support" in output
        assert "Overall" in output
        assert "0.95" in output or "0.94" in output  # Average recall

    def test_prints_no_results_message(self):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_summary_table([])
            output = mock_stdout.getvalue()

        assert "No results" in output

    def test_handles_missing_metrics(self):
        results = [
            {
                "inputs.category": "test",
                "outputs.function_call.function_call_recall": None,
                "outputs.function_call.function_call_precision": 1.0,
            }
        ]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_summary_table(results)
            output = mock_stdout.getvalue()

        assert "N/A" in output
        assert "1.00" in output


class TestTransportFactory:
    def test_create_without_headers(self):
        factory = TransportFactory(endpoint="ws://localhost:8000/ws")
        transport = factory.create()
        assert transport.url == "ws://localhost:8000/ws"
        assert transport.headers == {}

    def test_create_with_headers(self):
        headers = {"Authorization": "Bearer token"}
        factory = TransportFactory(endpoint="ws://localhost:8000/ws", headers=headers)
        transport = factory.create()
        assert transport.url == "ws://localhost:8000/ws"
        assert transport.headers == headers

    def test_create_multiple_transports(self):
        factory = TransportFactory(endpoint="ws://localhost:8000/ws")
        transport1 = factory.create()
        transport2 = factory.create()
        assert transport1 is not transport2
