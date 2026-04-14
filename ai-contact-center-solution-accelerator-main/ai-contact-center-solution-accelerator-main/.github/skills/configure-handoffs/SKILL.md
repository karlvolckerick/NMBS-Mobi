---
name: configure-handoffs
description: Set up call transfer routes between agents. Use when asked to add handoffs, transfers, or routing between agents in config.yaml.
---

# Set Up Handoffs Between Agents

You are a configuration assistant helping the user define handoffs in `config.yaml`.

Start by briefly explaining: "A handoff is when one agent transfers a call to another — for example, the receptionist
transferring a billing question to the billing agent." If the user asks for more detail, explain that you define which
agents are allowed to transfer to which, and that handoffs happen seamlessly during the conversation.

## Before You Start

Read `config.yaml` and summarise the current state:

- List the existing agents by name
- List existing handoffs (e.g., "receptionist can transfer to billing and support")
- Highlight any agents that have no handoffs configured
- Example: "You have 3 agents. The receptionist can transfer to billing and support. Billing and support can both
  transfer back to the receptionist and to each other."

## Questions

Ask these one at a time. Use numbered options wherever possible.

### 1. From Agent

Ask: "Which agent should be able to transfer calls?"

Show a numbered list of all agents.

### 2. To Agent

Ask: "Which agent should they transfer to?"

Show a numbered list of remaining agents (exclude the one picked in step 1, since an agent cannot hand off to itself).

**Validation:** If this exact handoff (same from/to pair) already exists, inform the user and ask if they want to pick a
different combination.

### 3. Description

Suggest a default description based on the target agent's description field. For example, if the target is "billing"
with description "A billing specialist who handles payment and account questions", suggest:

"Transfer to billing for payment and account questions"

Ask: "I suggest this description: '[suggestion]'. Does this work? (yes/no)"

If no, ask them to provide their own.

### 4. Bidirectional

Ask: "Should [to_agent] also be able to transfer back to [from_agent]? (yes/no)"

Default: yes

If yes, automatically generate the reverse handoff with an appropriate description.

**Validation:** If the reverse handoff already exists, inform the user and skip creating a duplicate.

### 5. Add More

Ask: "Would you like to add another handoff? (yes/no)"

If yes, go back to step 1. If no, proceed to apply.

## Apply the Change

Present all handoffs that will be added:

```yaml
  - from: "agent_a"
    to: "agent_b"
    description: "Transfer to agent_b for X"

  - from: "agent_b"
    to: "agent_a"
    description: "Transfer to agent_a for Y"
```

Ask: "Here are the handoffs I'll add. Does this look right? (yes/no)"

If yes:

- Add the new handoff entries to the `handoffs` list in `config.yaml`
- Do NOT modify any other section
- Confirm: "Done! [N] handoff(s) added to config.yaml."

If no, ask what they'd like to change.

## Suggest Evaluation

After the configuration is applied, check whether the evaluation scenarios cover the agents involved in the new handoff(s):

1. Read `eval/scenarios.jsonl`. Each line is a JSON object with a `category` field used for grouping results. By convention, categories are typically aligned with agent or domain names (e.g., "billing", "receptionist").
2. Collect the unique agent names from all handoffs that were just added (both `from` and `to` agents).
3. Check which of those agents have at least one scenario with a `category` matching (or closely related to) their name.

**If all involved agents have matching scenarios**, say:

> "Now that you've set up these handoffs, it's a good idea to run an evaluation to check how the transfers work. I can see there are already evaluation scenarios covering the agents involved. Would you like to run an eval? (yes/no)"
>
> - If yes → use the `eval` skill.
> - If no → acknowledge and finish.

**If some or all involved agents have no matching scenarios**, list the agents without coverage and say:

> "Now that you've set up these handoffs, it's a good idea to run an evaluation — but I noticed there are no evaluation scenarios in `eval/scenarios.jsonl` for these agents: [list]. You'll need to add scenarios that test those agents (and ideally the handoff between them) before an eval will be useful.
>
> Would you like help adding evaluation scenarios for the uncovered agents? (yes/no)"
>
> - If yes → help them add scenario lines to `eval/scenarios.jsonl` following the existing format (JSON-per-line with `scenario_name`, `category`, `instructions`, `expected_function_calls`, `unexpected_function_calls`), then suggest running the eval using the `eval` skill.
> - If no → acknowledge and finish.

## Important Rules

- Only add to the `handoffs` section. Never modify other sections.
- Never create a handoff where from and to are the same agent.
- Never create duplicate handoffs (same from/to pair).
- Preserve existing YAML formatting and comments.
