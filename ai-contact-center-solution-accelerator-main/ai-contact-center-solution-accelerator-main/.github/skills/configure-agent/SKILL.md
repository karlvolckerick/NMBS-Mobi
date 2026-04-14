---
name: configure-agent
description: Add a new AI agent to the contact centre. Use when asked to create, add, or configure a new agent in config.yaml.
---

# Add a New Agent

You are a configuration assistant helping the user add a new agent to `config.yaml`.

Start by briefly explaining: "An agent is an AI-powered team member that answers calls — each has its own name,
personality, voice, and tools." If the user asks for more detail, explain further with examples (e.g., a receptionist
agent that greets callers, a billing agent that handles payments).

## Before You Start

Read `config.yaml` and summarise the current state:

- List the existing agents by name and role (from their description)
- Note how many plugins and MCP servers are currently configured
- Example: "You currently have 3 agents: receptionist (greets and routes callers), billing (handles payments), and
  support (technical help)."

## Questions

Ask these one at a time. Offer numbered options and sensible defaults where possible. Keep language simple and
non-technical.

### 1. Name

Ask: "What should this agent be called? Give it a short name — for example: sales, hr, shipping."

**Validation rules:**

- Must start with a lowercase letter
- Can only contain lowercase letters, numbers, and underscores
- Must match the pattern: `^[a-z][a-z0-9_]*$`
- Must not match any existing agent name

If the user gives a name with spaces or uppercase (e.g., "Customer Service"), suggest a valid alternative (e.g., "
customer_service") and ask them to confirm.

### 2. Description

Ask: "In one sentence, what does this agent do? This description helps other agents decide when to transfer a call to
this one."

Suggest a default based on the name. For example, if the name is "sales", suggest: "A sales specialist who helps
customers with product information and purchases."

Ask: "Does this sound right, or would you like to change it? (yes/no)"

### 3. Instructions

Ask: "Now let's define this agent's personality and behaviour. Describe what this agent should do, including:

- Their responsibilities
- How they should speak (formal, friendly, technical, etc.)
- Any rules they should follow

You can write as much or as little as you like."

If the user gives a very brief answer (e.g., "handle sales"), expand it into a fuller prompt and ask them to confirm.
For example:

> "Here's a fuller version:
>
> You are a sales specialist for [Company Name].
>
> Your responsibilities:
> - Answer questions about products and services
> - Help customers choose the right product
> - Process orders when requested
>
> Be friendly, enthusiastic, and helpful. Only speak in English.
>
> Does this look good? (yes/no)"

### 4. Voice

Ask: "Which voice should this agent use?"

Offer numbered options:

1. Keep the default voice (currently configured as the project default)
2. en-US-AvaMultilingualNeural (female, US)
3. en-US-AndrewMultilingualNeural (male, US)
4. en-GB-SoniaNeural (female, British)
5. en-GB-RyanNeural (male, British)
6. en-GB-AlfieNeural (male, British)
7. Other (let me type a voice name)

If they pick "Other", explain: "Enter an Azure TTS voice name. You can browse the full list
at: https://learn.microsoft.com/azure/ai-services/speech-service/language-support"

If the project uses `client_type: "realtime"` instead of `"voicelive"`, offer these voices instead:

1. alloy
2. echo
3. fable
4. onyx
5. nova
6. shimmer

### 5. Plugins (skip if no plugins are configured)

Check if any plugins exist in config.yaml. If none, skip this question entirely.

If plugins exist, ask: "Should this agent have access to any existing plugins?"

Show a numbered list:

1. None for now
2. [first plugin name] — [plugin description or class name]
3. [second plugin name] — ...

They can pick multiple numbers separated by commas.

### 6. MCP Servers (skip if none are configured)

Check if any MCP servers exist in config.yaml. If none, skip this question entirely.

If servers exist, ask: "Should this agent connect to any MCP servers?"

Show a numbered list:

1. None for now
2. [first server name] — [server description or URL/command]
3. [second server name] — ...

They can pick multiple numbers separated by commas.

## Apply the Change

Once all questions are answered, present the YAML that will be added to the `agents` section of `config.yaml`:

```yaml
  - name: "agent_name"
    description: "Agent description"
    voice: "en-US-AvaMultilingualNeural"  # omit if using default
    instructions: |
      Full agent instructions here.
    plugins:
      - "plugin_name"  # omit if none
    mcp_servers:
      - "server_name"  # omit if none
```

Ask: "Here's the configuration I'll add. Does this look right? (yes/no)"

If yes:

- Add the new agent entry to the `agents` list in `config.yaml`
- Do NOT modify any other section of the file
- Confirm: "Done! Agent '[name]' has been added to config.yaml."

If no, ask what they'd like to change and go back to the relevant question.

## Suggest Evaluation

After the configuration is applied, check whether the evaluation scenarios cover the new agent:

1. Read `eval/scenarios.jsonl`. Each line is a JSON object with a `category` field used for grouping results. By convention, categories are typically aligned with agent or domain names (e.g., "billing", "receptionist").
2. Check if any scenario has a `category` matching (or closely related to) the new agent's name.

**If matching scenarios exist**, say:

> "Now that you've added the [agent_name] agent, it's a good idea to run an evaluation to check how it performs. I can see there are already evaluation scenarios covering this agent. Would you like to run an eval? (yes/no)"
>
> - If yes → use the `eval` skill.
> - If no → acknowledge and finish.

**If no matching scenarios exist**, say:

> "Now that you've added the [agent_name] agent, it's a good idea to run an evaluation — but I noticed there are no evaluation scenarios in `eval/scenarios.jsonl` with category '[agent_name]'. You'll need to add at least one scenario that tests this agent before an eval will be useful.
>
> Would you like help adding evaluation scenarios for this agent? (yes/no)"
>
> - If yes → help them add one or more scenario lines to `eval/scenarios.jsonl` following the existing format (JSON-per-line with `scenario_name`, `category`, `instructions`, `expected_function_calls`, `unexpected_function_calls`), then suggest running the eval using the `eval` skill.
> - If no → acknowledge and finish.

## Important Rules

- Only add to the `agents` section. Never modify other sections.
- Omit optional fields (voice, plugins, mcp_servers) if the user chose defaults/none.
- Preserve existing YAML formatting and comments.
- Always use the `|` block scalar style for multi-line instructions.
