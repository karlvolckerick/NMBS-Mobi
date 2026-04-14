# Customer Verification MCP Server

A minimal example MCP server that demonstrates how to connect an external service to the AI Contact Centre.

## What it does

Provides a single tool — `verify_customer` — that looks up customers by phone number. It uses a hardcoded dictionary of
3 fake customers, so no external dependencies are needed.

## Running

From the repository root:

```bash
task example-mcp-run
```

The server starts on `http://localhost:8001/mcp`.

## Connecting to the Contact Centre

Add to `config.yaml`:

```yaml
mcp_servers:
  - name: "customer_verification"
    transport: "http"
    url: "http://localhost:8001/mcp"
```

Then assign it to an agent:

```yaml
agents:
  - name: "receptionist"
    mcp_servers:
      - "customer_verification"
```

## Test data

| Phone           | Name          | Account Status |
|-----------------|---------------|----------------|
| +44 7700 900001 | Sarah Johnson | active         |
| +44 7700 900002 | James Smith   | active         |
| +44 7700 900003 | Emily Davis   | suspended      |

The suspended account is deliberate — it gives the agent something interesting to handle during demos.
