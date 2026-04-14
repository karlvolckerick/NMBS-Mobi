---
name: eval-results
description: Understand evaluation results, diagnose issues, and apply fixes. Use when asked to review eval results, explain scores, fix agent issues, or improve evaluation metrics.
---

# Review Evaluation Results

You are an evaluation analyst helping the user understand their evaluation results, diagnose issues, and apply fixes to
improve agent performance.

Start by briefly explaining: "I'll help you review your evaluation results, diagnose any issues, and suggest fixes. We'll
look at overall metrics, dig into failing scenarios, and apply targeted improvements."

## Before You Start

Check if `eval/outputs/evaluation_results.json` exists.

- **If it does NOT exist** → Tell the user: "No evaluation results found at `eval/outputs/evaluation_results.json`. You
  need to run evaluations first. Would you like me to help with that?" Then suggest using the `eval-run` skill.
- **If it exists** → Read the file and proceed to Step 1.

## Steps

Work through these steps one at a time. Confirm each step succeeds before moving on.

### 1. Read and Summarise Results

Read `eval/outputs/evaluation_results.json` and present the results in two parts.

**Part A — Overall Summary:**

Calculate and present the aggregate metrics across all scenarios:

- **Precision** — average across all scenarios
- **Recall** — average across all scenarios
- **F1 Score** — average across all scenarios
- **Intent Resolution** — average across all scenarios
- **Coherence** — average across all scenarios

Compare each metric against production targets and flag anything below threshold:

| Metric | Target | Status |
|--------|--------|--------|
| Intent Resolution | ≥ 4.0 | ✅ or ❌ |
| Coherence | ≥ 4.0 | ✅ or ❌ |
| F1 Score | ≥ 0.85 | ✅ or ❌ |

Use ✅ for metrics meeting or exceeding the target and ❌ for metrics below.

**Part B — Per-Scenario Breakdown:**

For each scenario, show:

- Scenario name and category
- Key metrics (precision, recall, F1, intent resolution, coherence, faults)
- Pass/fail status based on whether ALL of these thresholds are met:
  - Intent Resolution ≥ 4.0
  - Coherence ≥ 4.0
  - F1 ≥ 0.85
  - Faults = 0

Highlight scenarios that need attention — those that fail any threshold.

If all scenarios pass, congratulate the user: "All scenarios are meeting production targets! Your agents are performing
well." and skip to Step 5.

If any scenarios fail, proceed to Step 2.

### 2. Diagnose Issues

For each failing scenario:

1. Read the corresponding transcript from `eval/outputs/transcripts/{scenario_name}.json`.
2. Identify the root cause by matching the scenario's metrics against the diagnostic patterns below.
3. Present each diagnosis clearly with:
   - **Scenario** — which scenario failed
   - **Scores** — the actual metric values
   - **Evidence** — what the transcript shows (quote relevant parts)
   - **Diagnosis** — what the root cause likely is
   - **Recommended fix** — the specific change to make

Use the diagnostic patterns table in the Reference section below to match patterns to diagnoses.

### 3. Suggest Fixes

After diagnosing all failing scenarios, compile ALL fixes into a single numbered list. Categorise each fix as either
**config** or **code**:

- **`[config]` fixes** — changes to `config.yaml`, `eval/config.yaml`, or `eval/scenarios.jsonl` that this skill can
  apply directly:
  - **Agent instruction fix** — exact text to add or change in an agent's `instructions` field in `config.yaml`
  - **Turn detection fix** — specific setting to change in `config.yaml` (e.g., `silence_duration_ms: 1200`)
  - **Scenario fix** — updated scenario line for `eval/scenarios.jsonl`
  - **Handoff fix** — handoff entry to add or modify in `config.yaml`

- **`[code]` fixes** — changes to Python source code that must be delegated to the coding workflow:
  - **Tool implementation fix** — bug or missing behaviour in a tool's Python code
  - **Evaluator fix** — changes needed to an evaluator
  - **Agent orchestration fix** — issues in the agent setup code

Present the list like this:

> **Suggested fixes:**
>
> 1. `[config]` **Agent instruction fix** — Add "only call get_office_hours once per conversation" to the receptionist
>    agent's instructions in `config.yaml`.
> 2. `[config]` **Turn detection fix** — Increase `silence_duration_ms` from 800 to 1200 in `config.yaml`.
> 3. `[code]` **Tool implementation fix** — The `get_account_balance` tool is returning stale data because it doesn't
>    refresh the cache. Fix in `src/ai_contact_centre_solution_accelerator/tools/`.

For **config fixes**, ask:

> "Would you like me to apply the config fixes? I can apply all of them, or you can pick specific ones by number.
> (all / pick numbers / none)"

For **code fixes**, explain:

> "The code fixes require Python changes with proper tests. These will be handed back to the conductor to go through the
> standard coding workflow (plan → implement → code review) with TDD."

### 4. Apply Fixes

**Config fixes** (handled directly by this skill):

- If the user says "all", apply all config fixes sequentially.
- If the user picks numbers, apply only those.
- For each fix:
  1. Show what will change (before → after diff).
  2. Apply the change to the file.
  3. Confirm: "✅ Applied fix #N to `[file]`."

**Code fixes** (delegated to the conductor):

- For each code fix the user approves, hand back to the conductor with a clear description of:
  - The diagnosed problem (with evidence from eval results and transcripts)
  - The specific code change needed
  - Which files are likely affected
- The conductor then uses the standard orchestrated workflow: planning-subagent → implement-subagent →
  spec-review-subagent → code-review-subagent.

After all config fixes are applied, proceed to Step 5 to restart and re-evaluate.

### 5. Restart and Re-evaluate

After applying config fixes, restart the app and re-run evaluations yourself:

1. Stop the currently running app (kill the background terminal running `task run`).
2. Start the app again by running `task run` in a **background terminal**.
3. Wait a few seconds, then confirm it's listening on port 8000 (`lsof -i :8000`).
4. Tell the user: "App restarted with the updated config. Running evaluations now..."
5. Run `task eval-run` and wait for it to complete.
6. When results are ready, go back to **Step 1** to review the new scores and check if the fixes worked.

Do NOT ask the user to restart the app or re-run evals manually — do it yourself.

## Reference: Production Targets

These are the minimum scores for production readiness:

| Metric | Target |
|--------|--------|
| Intent Resolution | ≥ 4.0 |
| Coherence | ≥ 4.0 |
| F1 Score | ≥ 0.85 |
| Faults | 0 |

## Reference: Metric Thresholds

Use these thresholds when describing score quality to the user:

| Metric | Excellent | Good | Needs Improvement |
|--------|-----------|------|-------------------|
| Intent Resolution | ≥ 4.5 | 4.0 – 4.4 | < 4.0 |
| Coherence | ≥ 4.5 | 4.0 – 4.4 | < 4.0 |
| F1 Score | ≥ 0.95 | 0.85 – 0.94 | < 0.85 |
| Precision | ≥ 0.95 | 0.80 – 0.94 | < 0.80 |
| Recall | ≥ 0.95 | 0.80 – 0.94 | < 0.80 |
| Faults | 0 | 0 | > 0 |

## Reference: Diagnostic Patterns

Use this table to match a failing scenario's metrics to a likely root cause and fix:

| Pattern | Diagnosis | Likely Fix |
|---------|-----------|------------|
| High precision, low recall | Agent is cautious — misses actions | Add clearer instructions about when to call functions |
| Low precision, high recall | Agent is overeager — repeats actions | Add "only call X once" to agent instructions |
| Very low precision (e.g., 0.06) with recall 1.0 | Function called many times | Likely turn detection issue OR agent re-calling on every turn. Check transcript for repeated calls, then fix agent instructions or adjust `silence_duration_ms` |
| Faults > 0 | Agent calls forbidden functions | Add explicit "never call X" to agent instructions |
| Low intent resolution on handoff turn | Handoff message doesn't address intent | Improve handoff description or agent instructions about what to say during handoff |
| Low coherence | Disjointed conversation | Review agent instructions for clarity; check if agent is repeating itself |
| N/A scores | Evaluator error | Check Azure auth, check `chat_deployment` config |

## Troubleshooting

- **No results file found** → Run evaluations first with `task eval-run` (use the `eval-run` skill).
- **N/A scores in results** → Usually means Azure authentication failed for the evaluator's LLM calls. Run
  `az account show` to verify authentication.
- **Transcript file missing for a scenario** → The scenario may have crashed before completion. Re-run evaluations and
  check terminal output for errors.
- **Scores don't improve after fixes** → Double-check the change was applied correctly. Restart the app to pick up
  `config.yaml` changes. Try a more targeted fix based on the transcript evidence.

## Important Rules

- Always read the actual evaluation results and transcripts before diagnosing. Do not guess.
- Quote specific evidence from transcripts when presenting a diagnosis.
- Clearly label every fix as `[config]` or `[code]` — never mix them.
- Only apply config fixes that the user explicitly approves.
- Never modify Python source code directly — delegate code fixes to the conductor for proper TDD implementation.
- Show before → after diffs for every config change before applying.
- After applying fixes, always remind the user to restart the app and re-run evaluations.
