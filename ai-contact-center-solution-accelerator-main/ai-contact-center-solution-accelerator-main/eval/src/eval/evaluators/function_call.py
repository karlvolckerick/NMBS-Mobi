import logging

logger = logging.getLogger(__name__)


class FunctionCallEvaluator:
    """Evaluates function call precision, recall, F1 and faults.

    Compares actual function calls (from WebSocket events) against
    expected and unexpected function calls from the scenario definition.
    Comparison is on (plugin, function_name) tuples.
    """

    def __call__(
        self,
        *,
        function_calls: list[dict] | None,
        expected_function_calls: list[dict],
        unexpected_function_calls: list[dict],
        **kwargs,
    ) -> dict:
        if function_calls is None:
            return {
                "function_call_precision": None,
                "function_call_recall": None,
                "function_call_f1": None,
                "function_call_faults": None,
            }

        actual = [(fc["plugin"], fc["function"]) for fc in function_calls]
        expected = [(fc["plugin"], fc["function_name"]) for fc in expected_function_calls]
        unexpected = [(fc["plugin"], fc["function_name"]) for fc in unexpected_function_calls]

        matches = self._count_common(actual, expected)
        faults = self._count_common(actual, unexpected)

        precision = matches / len(actual) if actual else 0
        recall = matches / len(expected) if expected else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        return {
            "function_call_precision": precision,
            "function_call_recall": recall,
            "function_call_f1": f1,
            "function_call_faults": faults,
        }

    @staticmethod
    def _count_common(list1: list, list2: list) -> int:
        pool = list1.copy()
        count = 0
        for item in list2:
            if item in pool:
                pool.remove(item)
                count += 1
        return count
