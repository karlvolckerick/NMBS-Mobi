# AI Contact Centre Evaluation Module

End-to-end voice evaluation for the AI Contact Centre Solution Accelerator.

## Overview

This module runs automated evaluation scenarios that simulate real customer conversations and measure how well
the AI agents perform. It's essential for validating changes before production deployment.

**What it does:**
1. Connects to the running accelerator via WebSocket
2. Simulates customers using an LLM that follows scenario instructions
3. Converts customer text to speech and sends audio to the accelerator
4. Transcribes agent responses
5. Captures function calls and agent handoffs
6. Scores conversation quality using Azure AI Evaluation SDK

## Quick Start

### Prerequisites

Before running evaluations, ensure you have:

- **Running accelerator instance** - Start with `task run` from the project root (see [main README](../README.md))
- **Azure CLI authenticated** - Run `az login`
- **Terraform infrastructure deployed** - The eval module uses the same Azure OpenAI resource

The Terraform deployment creates all required model deployments:
| Deployment | Purpose |
|------------|---------|
| `gpt-4.1` | Customer LLM (generates customer responses) |
| `tts` | Text-to-speech (converts customer text to audio) |
| `gpt-4o-transcribe` | Transcription (converts agent audio to text) |

### Installation

From the project root:
```bash
task deps  # Installs all dependencies including eval module
```

### Configuration

The eval module has its own configuration file. Edit `eval/config.yaml`:

```yaml
target:
  endpoint: "ws://localhost:8000/ws"  # Your running accelerator

azure_openai:
  endpoint: "https://your-instance.openai.azure.com/"  # Same as main app
  chat_deployment: "gpt-4.1"           # For customer simulation
  tts_deployment: "tts"                 # For customer voice
  transcription_deployment: "gpt-4o-transcribe"  # For agent transcription
```

Get your endpoint from Terraform:
```bash
cd infra && terraform output openai_endpoint && cd ..
```

### Running Evaluations

```bash
# Terminal 1: Start the accelerator
task run

# Terminal 2: Run evaluation
task eval-run

# Or run with parallel scenarios (faster)
task eval-run-parallel
```

## Scenario Format

Scenarios are defined in JSONL format (`scenarios.jsonl`). Each line is a JSON object describing one test case:

```json
{
  "scenario_name": "billing_check_balance",
  "category": "billing",
  "instructions": "You want to check your account balance. Your account number is ACC001. After receiving the balance information, thank the agent and say goodbye.",
  "expected_function_calls": [
    {"plugin": "BillingPlugin", "function_name": "get_account_balance"}
  ],
  "unexpected_function_calls": [
    {"plugin": "BillingPlugin", "function_name": "process_payment"}
  ],
}
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `scenario_name` | Yes | Unique identifier (used in output filenames) |
| `category` | Yes | Grouping label for result aggregation |
| `instructions` | Yes | Prompt describing the customer's goal and behavior |
| `expected_function_calls` | Yes | Functions that SHOULD be called `[{plugin, function_name}]` |
| `unexpected_function_calls` | Yes | Functions that should NOT be called |

### Writing Good Scenarios

**Do:**
- Be specific: Include account numbers, order IDs, or other data the customer would provide
- Define exit conditions: Tell the customer when to say goodbye
- Keep it focused: Each scenario should test one specific flow
- Use natural language: Write instructions as you would brief a human actor

**Don't:**
- Make scenarios too complex (testing multiple flows)
- Forget to include expected function calls (metrics will be meaningless)

**Example of good vs bad:**

```json
// Good - specific, has exit condition
{
  "instructions": "You want to check your account balance. Your account number is ACC001. After receiving the balance, say goodbye."
}

// Bad - vague, no exit condition, or specific details
{
  "instructions": "You are an angry customer who calls about their account."
}
```

## Evaluators

### Function Call Evaluator (Custom)

Measures how accurately the agent uses tools:

| Metric | Formula | Meaning |
|--------|---------|---------|
| **Precision** | correct_calls / total_calls | "When the agent called a function, was it the right one?" |
| **Recall** | correct_calls / expected_calls | "Did the agent call all the functions it should have?" |
| **F1** | 2 × (P × R) / (P + R) | Harmonic mean balancing precision and recall |
| **Faults** | count(unexpected_calls) | Number of calls to functions that shouldn't be called |

### Intent Resolution (Azure AI SDK)

Scores 1-5 on whether the agent correctly identified and resolved the user's intent.

See [Azure AI Evaluation - Intent Resolution](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/evaluation-evaluators/agent-evaluators#intent-resolution)
for detailed methodology.

### Coherence (Azure AI SDK)

Scores 1-5 on conversation naturalness and logical flow.

See [Azure AI Evaluation - Coherence](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/evaluation-evaluators/general-purpose-evaluators#coherence)
for detailed methodology.

## Understanding Scores

### Function Call Metrics

| Metric | Excellent | Good | Needs Improvement |
|--------|-----------|------|-------------------|
| Precision | > 0.95 | 0.80 - 0.95 | < 0.80 |
| Recall | > 0.95 | 0.80 - 0.95 | < 0.80 |
| F1 | > 0.90 | 0.75 - 0.90 | < 0.75 |
| Faults | 0 | 0 | > 0 |

**Interpreting patterns:**
- **High precision, low recall**: Agent is cautious - misses some actions it should take
- **Low precision, high recall**: Agent is overeager - takes extra unnecessary actions
- **Both low**: Agent doesn't understand when to act
- **Faults > 0**: Serious issue - agent is doing things it shouldn't

### Conversation Quality Metrics

| Score | Intent Resolution | Coherence |
|-------|-------------------|-----------|
| **5** | Fully resolved user's request | Natural, flowing conversation |
| **4** | Resolved with minor gaps | Mostly natural, minor awkwardness |
| **3** | Partially resolved | Some confusing exchanges |
| **2** | Attempted but failed | Often unclear or disjointed |
| **1** | Did not address intent | Incoherent |

**Production targets:**
- Intent Resolution: ≥ 4.0 average
- Coherence: ≥ 4.0 average
- Function Call F1: ≥ 0.85

### What "N/A" Means

If you see N/A for Intent Resolution or Coherence:
- **Authentication issue**: Run `az login` to refresh credentials
- **Missing chat deployment**: Verify `chat_deployment` in `eval/config.yaml`
- **Conversation format issue**: The evaluator expects alternating user/assistant messages

Check the logs for specific error messages.

## Output

Results are written to the output directory (default: `eval/outputs/`):

```
outputs/
├── evaluation_results.json  # Full results with all metrics
└── transcripts/
    └── {scenario_name}.json # Individual conversation transcripts
```

### Summary Table

The CLI prints an aggregated summary after evaluation:

```
Category     Scenarios  FC Recall  FC Prec     Intent  Coherence
────────────────────────────────────────────────────────────────
billing      5          0.95       1.00        4.20    4.50
support      3          1.00       1.00        4.60    4.80
handoff      4          0.88       0.92        3.80    4.10
────────────────────────────────────────────────────────────────
Overall      12         0.94       0.97        4.20    4.50
```

### Reviewing Transcripts

Each scenario generates a transcript file showing the full conversation:

```json
{
  "transcript": [
    {"role": "user", "content": "I'd like to check my account balance."},
    {"role": "assistant", "content": "I can help with that. May I have your account number?"},
    {"role": "user", "content": "It's ACC001."},
    {"role": "assistant", "content": "Your balance is $5,250.00. Is there anything else?"}
  ],
  "function_calls": [
    {"agent": "billing", "plugin": "BillingPlugin", "function": "get_account_balance"}
  ]
}
```

Use these to debug when scenarios fail.

## Configuration Reference

### Target

```yaml
target:
  endpoint: "ws://localhost:8000/ws"  # WebSocket endpoint of running accelerator
  headers: {}                          # Optional headers (e.g., for authentication)
```

### Azure OpenAI

```yaml
azure_openai:
  endpoint: "https://your-instance.openai.azure.com/"
  api_version: "2024-12-01-preview"
  chat_deployment: "gpt-4.1"              # Customer LLM
  tts_deployment: "tts"                    # Customer voice synthesis
  transcription_deployment: "gpt-4o-transcribe"  # Agent response transcription
```

### Conversation

```yaml
conversation:
  max_turns: 15                      # Maximum customer-agent exchanges before timeout
  voice: "alloy"                     # TTS voice for simulated customer
  greeting_wait_seconds: 5           # Time to wait for initial agent greeting
  silence_timeout_seconds: 10        # Max silence before assuming agent is done
```

### Execution

```yaml
execution:
  concurrency: 1                     # Parallel scenarios (increase for speed)
  output_dir: "outputs"              # Results directory
```

## Troubleshooting

### Evaluators Return N/A

**Problem**: Intent Resolution and Coherence columns show "N/A"

**Solutions**:
1. Verify Azure authentication: `az login`
2. Check `chat_deployment` exists in `eval/config.yaml`
3. Ensure conversation has alternating user/assistant messages
4. Check logs for "Either 'conversation' or individual inputs must be provided" error

### Function Call Precision is Very Low

**Problem**: Precision like 0.06 when recall is 1.0

**Cause**: The same function is being called multiple times (e.g., 15 times instead of once)

**Solutions**:
1. Check agent instructions - ensure they don't cause repeated lookups
2. Review turn detection settings - agent may be responding multiple times
3. Adjust `silence_timeout_seconds` to better detect conversation end

### Scenarios Time Out

**Problem**: Scenarios hit max_turns without completing

**Solutions**:
1. Ensure scenario instructions include exit condition ("say goodbye")
2. Check agent is properly responding (review transcripts)
3. Increase `max_turns` if conversations legitimately need more exchanges

### WebSocket Connection Refused

**Problem**: `ConnectionRefusedError` when running evaluation

**Solutions**:
1. Ensure accelerator is running (`task run` in another terminal)
2. Verify `target.endpoint` matches where the accelerator is running
3. Check for port conflicts on 8000

## Development

```bash
# Run tests
task eval-test

# Lint
task eval-lint
```

## Architecture

```
eval/
├── src/eval/
│   ├── __main__.py              # CLI entry point
│   ├── config.py                # Configuration loading
│   ├── models.py                # Data models (TranscriptMessage, etc.)
│   ├── transport.py             # WebSocket client
│   ├── voice.py                 # TTS and transcription
│   ├── customer.py              # LLM-driven customer simulation
│   ├── conversation_simulator.py # Scenario execution
│   ├── runner.py                # Main evaluation pipeline
│   └── evaluators/
│       └── function_call.py     # Precision/recall evaluator
├── tests/                       # Unit tests
├── config.yaml                  # Evaluation configuration
└── scenarios.jsonl              # Test scenarios
```

### How It Works

1. **Runner** loads scenarios from JSONL and creates evaluation components
2. For each scenario, **ConversationSimulator**:
   - Connects to accelerator WebSocket
   - Waits for agent greeting (transcribes the audio)
   - Loops until exit condition or max turns:
     - **CustomerLLM** generates next response based on instructions + transcript history
     - **VoiceClient** converts text to audio (TTS) and sends to accelerator
     - Collects agent audio response
     - **VoiceClient** transcribes agent response
     - Captures function calls and agent switches from WebSocket events
   - Returns transcript, function calls, and metadata
3. **Evaluators** score each conversation:
   - Function call precision/recall/F1 (custom)
   - Intent resolution (Azure AI SDK)
   - Coherence (Azure AI SDK)
4. Results aggregated by category and written to output directory

### Adding Custom Evaluators

Create a new evaluator in `src/eval/evaluators/`:

```python
class MyEvaluator:
    def __call__(self, *, transcript: list, **kwargs) -> dict:
        # Your evaluation logic
        score = calculate_score(transcript)
        return {"my_metric": score}
```

Register in `runner.py`:
```python
evaluators = {
    "function_call": FunctionCallEvaluator(),
    "my_evaluator": MyEvaluator(),  # Add here
    ...
}
```
