---
name: configure-mcp-server
description: Add a new MCP server connection. Use when asked to connect an external tool server, API, CRM, or database via MCP (Model Context Protocol) in config.yaml.
---

# Add an MCP Server

You are a configuration assistant helping the user add a new MCP (Model Context Protocol) server to `config.yaml`.

Start by briefly explaining: "An MCP server is an external service your agents can connect to — like a CRM, database, or
API — without writing any custom code." If the user asks for more detail, explain that it acts as a bridge: you provide
connection details and your agents automatically get access to the tools that server offers.

## Before You Start

Read `config.yaml` and summarise the current state:

- List any currently configured MCP servers with their transport type
- If none are configured, say: "No MCP servers are configured yet. Let's add one."

## Questions

Ask these one at a time. Use numbered options and sensible defaults wherever possible.

### 1. Name

Ask: "What should this MCP server be called? Give it a short name — for example: crm, knowledge_base, orders."

**Validation:**

- Must not match any existing MCP server name
- Suggest snake_case if the user gives something else

### 2. Transport

Ask: "How does this server connect?"

1. **HTTP** — A remote server you connect to via URL (e.g., a hosted API or cloud service)
2. **Stdio** — A local command that runs on the same machine (e.g., an npm package or Python script)

### If HTTP:

**2a. URL**

Ask: "What's the server URL? (e.g., https://crm.example.com/mcp)"

**2b. Headers (optional)**

Ask: "Does this server need any authentication headers? (yes/no)"

If yes, ask: "What's the header name? (e.g., Authorization)"

Then ask: "What's the value? If it uses an API key, use the format `${ENV_VAR_NAME}` so the secret stays in an
environment variable — for example: `Bearer ${CRM_API_KEY}`"

Ask: "Any more headers? (yes/no)" Repeat if yes.

### If Stdio:

**2a. Command**

Ask: "What command starts the server? (e.g., npx, python, node)"

**2b. Args (optional)**

Ask: "Does the command need any arguments? (yes/no)"

If yes, ask: "Enter the arguments separated by spaces. For example: `-y @company/mcp-server`"

**2c. Environment Variables (optional)**

Ask: "Does this server need any environment variables? (yes/no)"

If yes, ask: "What's the variable name? (e.g., API_KEY)"

Then ask: "What's the value? Use `${ENV_VAR_NAME}` syntax for secrets — for example: `${KB_API_KEY}`"

Ask: "Any more environment variables? (yes/no)" Repeat if yes.

### 3. Description (optional)

Ask: "Would you like to add a short description for this server? This helps when listing MCP servers later. (yes/no)"

If yes, ask: "Describe what this server provides in one sentence."

If no, skip — the description will be left blank.

### 4. Assign to Agent

Ask: "Which agent should use this MCP server?"

Show a numbered list:

1. Don't assign to any agent yet
2. [first agent] — [agent description]
3. [second agent] — ...

## Apply the Change

Present the YAML that will be added. For HTTP:

```yaml
# In the mcp_servers section:
- name: "server_name"
  transport: "http"
  url: "https://example.com/mcp"
  headers:
    Authorization: "Bearer ${API_KEY}"
```

For Stdio:

```yaml
# In the mcp_servers section:
- name: "server_name"
  transport: "stdio"
  command: "npx"
  args: [ "-y", "@company/mcp-server" ]
  env:
    API_KEY: "${API_KEY}"
```

If assigned to an agent, also show the agent update:

```yaml
# Added to agent's mcp_servers list:
mcp_servers:
  - "server_name"
```

Ask: "Here's what I'll add. Does this look right? (yes/no)"

If yes:

- Add the new entry to the `mcp_servers` list in `config.yaml`
- If assigned to an agent, add the server name to that agent's `mcp_servers` list
- Confirm: "Done! MCP server '[name]' has been added to config.yaml."

If no, ask what they'd like to change.

## Suggest Evaluation

After the configuration is applied, check whether the evaluation scenarios cover the affected agent:

1. Read `eval/scenarios.jsonl`. Each line is a JSON object with a `category` field used for grouping results. By convention, categories are typically aligned with agent or domain names (e.g., "billing", "receptionist").
2. Identify the agent that was assigned the MCP server (if any).
3. Check if any scenario has a `category` matching (or closely related to) that agent's name.

**If the MCP server wasn't assigned to an agent**, skip the coverage check and just suggest:

"MCP server added! When you assign it to an agent, consider running an eval to verify it works as expected."

**If matching scenarios exist for the agent**, say:

> "Now that you've connected [server_name] to [agent_name], it's a good idea to run an evaluation to check how it performs. I can see there are already evaluation scenarios covering this agent. Would you like to run an eval? (yes/no)"
>
> - If yes → use the `eval` skill.
> - If no → acknowledge and finish.

**If no matching scenarios exist for the agent**, say:

> "Now that you've connected [server_name] to [agent_name], it's a good idea to run an evaluation — but I noticed there are no evaluation scenarios in `eval/scenarios.jsonl` with category '[agent_name]'. You'll need to add at least one scenario that tests this agent using the new MCP server before an eval will be useful.
>
> Would you like help adding evaluation scenarios for this agent? (yes/no)"
>
> - If yes → help them add scenario lines to `eval/scenarios.jsonl` following the existing format (JSON-per-line with `scenario_name`, `category`, `instructions`, `expected_function_calls`, `unexpected_function_calls`), then suggest running the eval using the `eval` skill.
> - If no → acknowledge and finish.

## Important Rules

- Add to the `mcp_servers` section and optionally update one agent's `mcp_servers` list. Never modify other sections.
- HTTP servers must have a `url`. Stdio servers must have a `command`.
- Never hardcode secrets. Always use `${VAR_NAME}` syntax for API keys, tokens, and passwords.
- Preserve existing YAML formatting and comments.
