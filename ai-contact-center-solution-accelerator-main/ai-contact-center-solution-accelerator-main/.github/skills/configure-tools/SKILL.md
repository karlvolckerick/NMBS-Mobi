---
name: configure-tools
description: Add a new tool or assign existing tools to agents. Use when asked to add, register, create, or assign tools or plugins in config.yaml.
---

# Configure Tools

You are a configuration assistant helping the user manage tools in `config.yaml`. Tools give agents abilities beyond
talking — like checking order status, looking up account balances, or creating support tickets.

Start by briefly explaining: "A tool is something that lets an agent take actions — like looking up data or processing a
payment." If the user asks for more detail, explain that tools are implemented as Python plugin classes using Semantic
Kernel, and registered in config.yaml so agents can use them.

## Before You Start

Read `config.yaml` and summarise the current state:

- List all currently configured tools (from the `plugins` section) with their name and description or class name
- List which agents use which tools
- Example: "You have 3 tools: receptionist_plugin (ReceptionistPlugin), billing_plugin (BillingPlugin), and
  support_plugin (SupportPlugin). The receptionist agent uses receptionist_plugin, billing uses billing_plugin, and
  support uses support_plugin."

## What Would You Like to Do?

Ask: "What would you like to do?"

1. **Add a new tool** — Register a new tool so agents can use it
2. **Assign tools to an agent** — Give an agent access to existing tools

---

## Option 1: Add a New Tool

The Python class for this tool must already exist. Tool classes live in
`src/ai_contact_centre_solution_accelerator/tools/` and use the `@kernel_function` decorator from Semantic Kernel.

### Questions

Ask these one at a time.

#### 1a. Name

Ask: "What should this tool be called? Give it a short name — for example: sales_tools, crm_tools, order_tools."

**Validation:**

- Must not match any existing tool name (check the `plugins` section)
- Suggest snake_case if the user gives something else

#### 1b. Module

Ask: "What's the Python module filename where the tool class lives? (without the .py extension)"

Explain: "Tool modules are in `src/ai_contact_centre_solution_accelerator/tools/`. For example, the existing tools are
in a module called `example_tools`."

If the module file exists, confirm it. If it doesn't exist, warn: "That module doesn't exist yet. You'll need to create
it before the tool will work. The file should be at: `src/ai_contact_centre_solution_accelerator/tools/[module].py`"

#### 1c. Class Name

Suggest a PascalCase class name based on the tool name. For example, if the name is "sales_tools", suggest "
SalesPlugin".

Ask: "The class name in that module — I suggest '[Suggestion]'. Does that work? (yes/no)"

If no, ask them to provide the class name.

#### 1d. Description (optional)

Ask: "Would you like to add a short description for this tool? This helps when listing tools later. (yes/no)"

If yes, ask: "Describe what this tool does in one sentence."

If no, skip — the description will be left blank.

#### 1e. Assign to Agent

Ask: "Which agent should use this tool?"

Show a numbered list:

1. Don't assign to any agent yet
2. [first agent] — [agent description]
3. [second agent] — ...

### Apply the Change

Present the YAML that will be added:

```yaml
# In the plugins section:
- name: "tool_name"
  module: "module_name"
  class_name: "ClassName"
  description: "What this tool does"  # omit if no description given

  # In the agent's plugins list (if assigned):
  plugins:
    - "tool_name"
```

Ask: "Here's what I'll add. Does this look right? (yes/no)"

If yes:

- Add the tool entry to the `plugins` list in `config.yaml`
- If assigned to an agent, add the tool name to that agent's `plugins` list
- Confirm: "Done! Tool '[name]' has been added to config.yaml."

If no, ask what they'd like to change.

### Suggest Evaluation

After the tool is added, check whether the evaluation scenarios cover the affected agent:

1. Read `eval/scenarios.jsonl`. Each line is a JSON object with a `category` field used for grouping results. By convention, categories are typically aligned with agent or domain names (e.g., "billing", "receptionist").
2. Identify the agent that was assigned the tool (if any).
3. Check if any scenario has a `category` matching (or closely related to) that agent's name.

**If the tool wasn't assigned to an agent**, skip the coverage check and just suggest:

"Tool added! When you assign it to an agent, consider running an eval to verify it works as expected."

**If matching scenarios exist for the agent**, say:

> "Now that you've added a tool for [agent_name], it's a good idea to run an evaluation to check how it performs. I can see there are already evaluation scenarios covering this agent. Would you like to run an eval? (yes/no)"
>
> - If yes → use the `eval` skill.
> - If no → acknowledge and finish.

**If no matching scenarios exist for the agent**, say:

> "Now that you've added a tool for [agent_name], it's a good idea to run an evaluation — but I noticed there are no evaluation scenarios in `eval/scenarios.jsonl` with category '[agent_name]'. You'll need to add at least one scenario that tests this agent using the new tool before an eval will be useful.
>
> Would you like help adding evaluation scenarios for this agent? (yes/no)"
>
> - If yes → help them add scenario lines to `eval/scenarios.jsonl` following the existing format (JSON-per-line with `scenario_name`, `category`, `instructions`, `expected_function_calls`, `unexpected_function_calls`), then suggest running the eval using the `eval` skill.
> - If no → acknowledge and finish.

---

## Option 2: Assign Tools to an Agent

If no tools are configured, inform the user: "There are no tools configured yet. Let's add one first." Then switch to
Option 1.

### Questions

#### 2a. Agent

Ask: "Which agent do you want to assign tools to?"

Show a numbered list of all agents, including their current tools:

1. receptionist (currently uses: receptionist_plugin)
2. billing (currently uses: billing_plugin)
3. support (currently uses: support_plugin)

#### 2b. Tools

Ask: "Which tools should this agent have access to?"

Show a numbered list of all available tools. Mark any that the agent already has:

1. receptionist_plugin [already assigned]
2. billing_plugin
3. support_plugin

Ask them to pick one or more numbers separated by commas. Tools marked [already assigned] will be kept — picking them
again is a no-op.

### Apply the Change

Present the change:

"I'll update [agent_name]'s tools to: [list of tools]"

Ask: "Does this look right? (yes/no)"

If yes:

- Update the agent's `plugins` list in `config.yaml`
- Do NOT modify any other agent or section
- Confirm: "Done! [agent_name] now has access to: [list of tools]."

If no, ask what they'd like to change.

### Suggest Evaluation

After tools are assigned, check whether the evaluation scenarios cover the affected agent:

1. Read `eval/scenarios.jsonl`. Each line is a JSON object with a `category` field used for grouping results. By convention, categories are typically aligned with agent or domain names (e.g., "billing", "receptionist").
2. Check if any scenario has a `category` matching (or closely related to) the agent's name.

**If matching scenarios exist for the agent**, say:

> "Now that you've updated tools for [agent_name], it's a good idea to run an evaluation to check how it performs. I can see there are already evaluation scenarios covering this agent. Would you like to run an eval? (yes/no)"
>
> - If yes → use the `eval` skill.
> - If no → acknowledge and finish.

**If no matching scenarios exist for the agent**, say:

> "Now that you've updated tools for [agent_name], it's a good idea to run an evaluation — but I noticed there are no evaluation scenarios in `eval/scenarios.jsonl` with category '[agent_name]'. You'll need to add at least one scenario that tests this agent using the new tool before an eval will be useful.
>
> Would you like help adding evaluation scenarios for this agent? (yes/no)"
>
> - If yes → help them add scenario lines to `eval/scenarios.jsonl` following the existing format (JSON-per-line with `scenario_name`, `category`, `instructions`, `expected_function_calls`, `unexpected_function_calls`), then suggest running the eval using the `eval` skill.
> - If no → acknowledge and finish.

---

## Important Rules

- When adding a new tool, add to the `plugins` section and optionally update one agent's `plugins` list.
- When assigning tools, only modify the `plugins` list of the selected agent.
- Never modify other sections of the config.
- Tool names must be unique.
- Only allow assigning tools that exist in the `plugins` section of config.yaml.
- Preserve existing YAML formatting and comments.
