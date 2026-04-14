import json
import logging
from pathlib import Path

from azure.ai.evaluation import CoherenceEvaluator, IntentResolutionEvaluator, evaluate
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI

from eval.config import EvalConfig
from eval.conversation_simulator import ConversationSimulator
from eval.customer import CustomerLLM
from eval.evaluators.function_call import FunctionCallEvaluator
from eval.transport import WebSocketTransport
from eval.voice import VoiceClient

logger = logging.getLogger(__name__)


def load_scenarios(path: Path) -> list[dict]:
    """Load scenarios from a JSONL file."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    scenarios = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                scenarios.append(json.loads(line))
    return scenarios


def print_summary_table(results: list[dict]) -> None:
    """Print an aggregated summary table to stdout."""
    if not results:
        print("No results.")
        return

    categories: dict[str, list[dict]] = {}
    for r in results:
        cat = r.get("inputs.category", "unknown")
        categories.setdefault(cat, []).append(r)

    header = f"{'Category':<15} {'Scenarios':>9} {'FC Recall':>10} {'FC Prec':>10} {'Intent':>10} {'Coherence':>10}"
    print(header)
    print("-" * len(header))

    all_results = []
    for cat, cat_results in sorted(categories.items()):
        all_results.extend(cat_results)
        n = len(cat_results)
        recall = _safe_mean([r.get("outputs.function_call.function_call_recall") for r in cat_results])
        prec = _safe_mean([r.get("outputs.function_call.function_call_precision") for r in cat_results])
        intent = _safe_mean([r.get("outputs.intent_resolution.intent_resolution") for r in cat_results])
        coherence = _safe_mean([r.get("outputs.coherence.coherence") for r in cat_results])
        print(f"{cat:<15} {n:>9} {recall:>10} {prec:>10} {intent:>10} {coherence:>10}")

    print("-" * len(header))
    n = len(all_results)
    recall = _safe_mean([r.get("outputs.function_call.function_call_recall") for r in all_results])
    prec = _safe_mean([r.get("outputs.function_call.function_call_precision") for r in all_results])
    intent = _safe_mean([r.get("outputs.intent_resolution.intent_resolution") for r in all_results])
    coherence = _safe_mean([r.get("outputs.coherence.coherence") for r in all_results])
    print(f"{'Overall':<15} {n:>9} {recall:>10} {prec:>10} {intent:>10} {coherence:>10}")


def _safe_mean(values: list) -> str:
    nums = [v for v in values if v is not None]
    if not nums:
        return "N/A"
    return f"{sum(nums) / len(nums):.2f}"


class TransportFactory:
    """Creates WebSocketTransport instances for each scenario."""

    def __init__(self, endpoint: str, headers: dict[str, str] | None = None) -> None:
        self._endpoint = endpoint
        self._headers = headers or {}

    def create(self) -> WebSocketTransport:
        return WebSocketTransport(url=self._endpoint, headers=self._headers)


def run(config: EvalConfig) -> None:
    """Run the full evaluation pipeline."""
    output_dir = Path(config.execution.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "transcripts").mkdir(exist_ok=True)

    dataset_path = Path(config.dataset)

    # Create Azure OpenAI client
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )
    openai_client = AsyncAzureOpenAI(
        azure_endpoint=config.azure_openai.endpoint,
        api_version=config.azure_openai.api_version,
        azure_ad_token_provider=token_provider,
    )

    # Build components
    transport_factory = TransportFactory(
        endpoint=config.target.endpoint,
        headers=config.target.headers,
    )
    voice_client = VoiceClient(
        openai_client=openai_client,
        tts_deployment=config.azure_openai.tts_deployment,
        transcription_deployment=config.azure_openai.transcription_deployment,
    )
    customer = CustomerLLM(
        openai_client=openai_client,
        chat_deployment=config.azure_openai.chat_deployment,
    )
    simulator = ConversationSimulator(
        transport_factory=transport_factory,
        voice_client=voice_client,
        customer=customer,
        conversation_config=config.conversation,
    )

    # Build evaluators
    model_config = {
        "azure_endpoint": config.azure_openai.endpoint,
        "azure_deployment": config.azure_openai.chat_deployment,
        "api_version": config.azure_openai.api_version,
    }

    evaluators = {
        "function_call": FunctionCallEvaluator(),
        "intent_resolution": IntentResolutionEvaluator(model_config=model_config),
        "coherence": CoherenceEvaluator(model_config=model_config),
    }

    evaluator_config = {
        "function_call": {
            "column_mapping": {
                "function_calls": "${target.function_calls}",
                "expected_function_calls": "${data.expected_function_calls}",
                "unexpected_function_calls": "${data.unexpected_function_calls}",
            }
        },
        "intent_resolution": {
            "column_mapping": {
                "conversation": "${target.conversation}",
            }
        },
        "coherence": {
            "column_mapping": {
                "conversation": "${target.conversation}",
            }
        },
    }

    logger.info("Starting evaluation with %d concurrency", config.execution.concurrency)

    result = evaluate(
        data=str(dataset_path),
        target=simulator,
        evaluators=evaluators,
        evaluator_config=evaluator_config,
        output_path=str(output_dir),
    )

    # Write individual transcripts
    rows = result.get("rows", [])
    for row in rows:
        name = row.get("inputs.scenario_name", "unknown")
        transcript_path = output_dir / "transcripts" / f"{name}.json"
        with open(transcript_path, "w") as f:
            json.dump(
                {
                    "transcript": row.get("outputs.transcript", []),
                    "function_calls": row.get("outputs.function_calls", []),
                },
                f,
                indent=2,
                default=str,
            )

    print_summary_table(rows)
    logger.info("Evaluation complete. %d scenarios processed.", len(rows))
