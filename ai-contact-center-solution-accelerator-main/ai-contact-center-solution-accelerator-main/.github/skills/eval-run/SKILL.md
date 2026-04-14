---
name: eval-run
description: Run evaluation scenarios against the accelerator. Use when asked to run evals, test agents, or evaluate agent performance.
---

# Run Evaluations

You are an evaluation assistant helping the user configure and run evaluation scenarios against the AI Contact Centre
Solution Accelerator.

Start by briefly explaining: "I'll help you run evaluations against your accelerator. We'll check prerequisites,
configure the eval settings, make sure the app is running, execute the scenarios, and review the results."

## Before You Start

Check the current state of the user's environment:

1. Check if `.venv/` exists — if it does, dependencies may already be installed.
2. Read `eval/config.yaml` and check whether the `azure_openai.endpoint` field still contains the placeholder `<>`. If
   it contains a real URL, configuration may already be done.
3. Check if port 8000 is already in use (`lsof -i :8000`) — the app may already be running.

Summarise what you found to the user, e.g.:

- "Dependencies look installed — `.venv/` exists."
- "The eval config still has a placeholder endpoint — we'll need to set that up."
- "The app is already running on port 8000, so we can skip that step."
- "Looks like a fresh setup — we'll start from the beginning."

Then proceed from the first incomplete step.

## Steps

Work through these steps one at a time. Confirm each step succeeds before moving on.

### 1. Prerequisites Check

Verify the development environment is ready:

1. Check that dependencies are installed by confirming `.venv/` exists. If not, run:
   ```
   task deps
   ```
2. Verify Azure CLI authentication:
   ```
   az account show
   ```
   Confirm the correct subscription is active.

**Troubleshooting:**
- `task: command not found` → Install [Task](https://taskfile.dev/) (`brew install go-task`).
- `az: command not found` → Install the [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli).
- `az account show` fails → Run `az login` to authenticate.

### 2. Configure eval/config.yaml

Read `eval/config.yaml` and check the `azure_openai.endpoint` field.

If it still contains the placeholder (`<>`):

1. Get the real endpoint from Terraform:
   ```
   cd infra && terraform output openai_endpoint
   ```
2. Update the `azure_openai.endpoint` field in `eval/config.yaml` with the returned URL.

Explain the other configuration fields and their defaults:

- **`target.endpoint`** — The WebSocket URL of the running accelerator. Default: `ws://localhost:8000/ws`. Only change
  if the app is running on a different host or port.
- **`dataset`** — The scenarios file to run. Default: `scenarios.jsonl`.
- **`conversation.max_turns`** — Maximum back-and-forth turns per scenario before the conversation is stopped. Default:
  `15`. Increase if scenarios need more turns to complete.
- **`conversation.voice`** — The TTS voice used for the simulated customer. Default: `alloy`.
- **`conversation.greeting_wait_seconds`** — How long to wait for the agent's greeting before starting. Default: `5`.
- **`conversation.silence_timeout_seconds`** — How long to wait for a response before treating it as silence. Default:
  `10`.
- **`execution.concurrency`** — Number of scenarios to run in parallel. Default: `1`. Only used by the parallel runner.
- **`execution.output_dir`** — Where results are written. Default: `outputs`.

Only change non-endpoint fields if the user explicitly asks to adjust them.

**Troubleshooting:**
- `terraform output` fails → Make sure you have run `terraform apply` first (see the `setup-local` skill).
- Endpoint looks wrong → It should be a URL like `https://<name>.cognitiveservices.azure.com/`.

### 3. Start the Accelerator

Check if the app is already running:

```
lsof -i :8000
```

If port 8000 is not in use, start the app yourself:

1. Run `task run` in a **background terminal**.
2. Wait a few seconds, then re-check `lsof -i :8000` to confirm the app is listening.
3. Tell the user: "I've started the accelerator — it's now running on port 8000."

Do NOT ask the user to start it manually — start it yourself.

**Troubleshooting:**
- `task run` fails → Check that `config.yaml` (the app config, not eval config) is valid and dependencies are installed.
- Port 8000 already in use by something else → Stop the other process or change the `target.endpoint` port in
  `eval/config.yaml` to match.

### 4. Review Scenarios

Before running, present the scenarios that will be executed so the user can review them.

1. Read the scenarios file from `eval/config.yaml` under `dataset` (defaults to `scenarios.jsonl`, resolved relative to
   `eval/`, i.e. `eval/scenarios.jsonl` from the repo root).
2. Present a summary table of all scenarios:

| # | Scenario | Category | Customer Goal | Expected Calls | Unexpected Calls |
|---|----------|----------|---------------|----------------|------------------|
| 1 | `scenario_name` | `category` | Brief summary of `instructions` | List of `plugin.function_name` | List (or "None") |

3. After the table, ask:

> "These are the scenarios that will be run. Would you like to proceed, or do you want to add, remove, or modify any
> scenarios before running? (proceed / modify)"

- **If proceed** → Move to Step 5.
- **If modify** → Help the user edit the dataset file referenced by `eval/config.yaml` (resolve the `dataset` path
  relative to `eval/`). Each line must be a valid JSON object with the fields: `scenario_name`, `category`,
  `instructions`, `expected_function_calls`, and `unexpected_function_calls`. After edits, re-read that file,
  re-present the updated table, and ask again.

### 5. Run Evaluation

Explain the two run modes:

1. **Sequential** (`task eval-run`) — Runs scenarios one at a time. Slower, but output is easier to follow and debug.
   Recommended for your first run.
2. **Parallel** (`task eval-run-parallel`) — Runs multiple scenarios concurrently (controlled by
   `execution.concurrency` in `eval/config.yaml`). Faster for large scenario sets.

Recommend sequential for the first run:

> "I'd recommend running sequentially first so we can see each scenario's output clearly. You can switch to parallel
> runs once things look good."

Run the chosen command:

```
task eval-run
```

or:

```
task eval-run-parallel
```

Monitor the output as it runs. After completion, a summary table will print showing per-scenario results including
evaluator scores and pass/fail status.

**Troubleshooting:**
- **WebSocket connection refused** → The app is not running on the expected port. Check that `task run` is active and
  the `target.endpoint` in `eval/config.yaml` matches.
- **Scenarios time out** → Increase `conversation.max_turns` in `eval/config.yaml`, or check that scenario exit
  conditions (in `scenarios.jsonl`) are reachable.
- **N/A evaluator scores** → This usually means Azure authentication failed for the evaluator's LLM calls. Run
  `az account show` to verify authentication.
- **Very low precision scores** → Often caused by repeated function calls. Check the transcript to see if the agent is
  calling the same tool multiple times in a loop.

### 6. Review Output

After the run completes:

1. Confirm results were written to `eval/outputs/`.
2. Show the user the summary metrics from the evaluation output.
3. Offer next steps:

> "Would you like me to help you understand these results and suggest improvements? I can use the eval-results skill
> for that."

**Troubleshooting:**
- No output files → Check that `execution.output_dir` in `eval/config.yaml` points to a valid directory and the run
  completed without crashing.

## Important Rules

- Work through steps sequentially. Do not skip ahead.
- Confirm each step succeeds before moving to the next.
- If a step fails, troubleshoot before continuing.
- Never modify application source code — this skill only handles evaluation configuration and execution.
- Only change non-endpoint fields in `eval/config.yaml` if the user explicitly asks.
