# Define Span Hierarchy and Attribute Conventions for Distributed Tracing

* **Status:** proposed
* **Proposer:** @weijenlu
* **Date:** 2026-02-11
* **Technical Story:** Align observability instrumentation with Azure AI Foundry trace-agent conventions and OpenTelemetry semantic conventions for gen_ai, ensuring traces are usable in both Foundry portal and Azure Monitor (Application Insights).

## Context and Problem Statement

The AI Contact Centre Solution Accelerator currently has **no distributed tracing**. Infrastructure provisions an Application Insights resource (see `infra/main.tf`), and Semantic Kernel brings `opentelemetry-api`/`opentelemetry-sdk` as transitive dependencies, but neither is wired up — no `TracerProvider` is configured, no exporter is set, and no spans are created.

Without a defined span hierarchy and attribute conventions, any future instrumentation will be inconsistent and hard to query. Aligning with Azure AI Foundry trace-agent concepts and the OpenTelemetry `gen_ai` semantic conventions ensures traces are usable in the Foundry portal, Azure Monitor, and any OTLP-compatible backend.

## Decision Drivers

* Traces must render correctly in **Azure AI Foundry Tracing** and **Application Insights End-to-end Transaction Details**
* Must follow **OpenTelemetry semantic conventions** for `gen_ai` spans (including the multi-agent extensions co-developed by Microsoft and Cisco/Outshift)
* Must leverage **Semantic Kernel's built-in OTel instrumentation** rather than duplicating it
* Must support debugging of the key workflows: WebSocket sessions, agent interactions, handoffs, and tool/function calls
* Error recording must be consistent and queryable
* This is a demo/accelerator app — data hygiene defaults to **allow-all** with an opt-in block list

## Considered Options

* **Option 1: WebSocket session as root span** — one trace per call, child spans for agents/tools/handoffs
* **Option 2: Per-message root spans** — each audio chunk or conversational turn starts a new trace, correlated by a shared `session.id` attribute

## Decision Outcome

Chosen option: **"WebSocket session as root span"**, because a single phone call is the natural unit of work in a contact centre. One trace per call makes it trivial to find "everything about this call" in App Insights. The WebSocket connection in `routes/call.py` has a clear connect/disconnect lifecycle that maps directly to a root span. Long-duration spans (minutes) are acceptable in Application Insights and Foundry.

---

## Span Taxonomy

Spans are listed from outermost (root) to innermost (leaf). Nesting is shown via indentation. The taxonomy follows the OpenTelemetry `gen_ai` agent span conventions (`invoke_agent`, `execute_tool`) where applicable.

### Span Hierarchy

```
ws.session                                          # Root span — full WebSocket lifetime
├── aoai.realtime.session                           # Azure OpenAI Realtime session (external)
├── agent.session (agent.name=triage)               # Time spent with one agent
│   ├── agent.response_turn                         # One conversational turn (user speaks → agent responds)
│   │   └── [Semantic Kernel auto-instrumented]     # LLM call spans from SK
│   ├── execute_tool (tool.name=verify_customer)    # Tool/function invocation
│   │   └── [MCP or plugin execution]               # Actual work
│   └── invoke_agent (handoff.to=billing)           # Handoff decision + switch
├── agent.session (agent.name=billing)              # Next agent takes over
│   ├── agent.response_turn
│   ├── execute_tool (tool.name=lookup_balance)
│   └── agent.response_turn
└── ws.disconnect                                   # Clean or error disconnect
```

### Span Definitions

| Span Name | Kind | Created At | Ends At | Description |
|-----------|------|------------|---------|-------------|
| `ws.session` | `SERVER` | `routes/call.py` — WebSocket accepted | WebSocket closed | Root span for entire call session |
| `agent.session` | `INTERNAL` | `orchestration.py` — agent becomes active | Agent is replaced by handoff, or session ends | Covers all activity under one agent |
| `agent.response_turn` | `INTERNAL` | `RESPONSE_CREATED` event from Realtime API | `RESPONSE_DONE` event | One request-response turn |
| `invoke_agent` | `INTERNAL` | `transfer_to_*` function called | `_switch_to_agent()` completes | Handoff from one agent to another (OTel `gen_ai` convention) |
| `execute_tool` | `CLIENT` | `on_function_call` callback fires | `on_function_result` callback fires | Tool/function execution (OTel `gen_ai` convention) |
| `aoai.realtime.session` | `CLIENT` | `orchestration.start()` | `orchestration.stop()` | Azure OpenAI Realtime API connection |
| `ws.disconnect` | `INTERNAL` | Disconnect initiated | Cleanup complete | Captures disconnect reason |

---

## Attributes

### Naming Conventions

All custom attributes use dotted namespaces. Follow OpenTelemetry `gen_ai.*` conventions where applicable, use `session.*` for session-scoped data, and `agent.*` / `tool.*` for domain-specific attributes.

### Required Attributes by Span

| Span | Attribute | Type | Example | Notes |
|------|-----------|------|---------|-------|
| `ws.session` | `session.id` | string | UUID | Unique per WebSocket connection |
| `ws.session` | `service.name` | string | `"ai-contact-centre"` | Set via `OTEL_SERVICE_NAME` env var |
| `ws.session` | `gen_ai.system` | string | `"openai"` | Per OTel semconv |
| `ws.session` | `gen_ai.request.model` | string | `"gpt-4o-realtime"` | From `config.yaml` `azure_openai.deployment` |
| `agent.session` | `agent.name` | string | `"triage"` | Agent name from config |
| `agent.session` | `agent.description` | string | `"Routes callers"` | Optional — agent description |
| `invoke_agent` | `handoff.from` | string | `"triage"` | Source agent name |
| `invoke_agent` | `handoff.to` | string | `"billing"` | Target agent name |
| `execute_tool` | `tool.name` | string | `"verify_customer"` | Function name |
| `execute_tool` | `tool.plugin` | string | `"CustomerPlugin"` | Plugin/MCP server name |
| `execute_tool` | `tool.call.arguments` | string | JSON string | Arguments passed |
| `execute_tool` | `tool.call.results` | string | JSON string | Result returned |
| All spans | `error.type` | string | `"WebSocketDisconnect"` | Exception class name (on error only) |

### Optional Attributes

| Attribute | Type | Where | Notes |
|-----------|------|-------|-------|
| `session.client_type` | string | `ws.session` | `"voicelive"` or `"realtime"` |
| `session.authenticated` | bool | `ws.session` | Whether ACS JWT was validated |
| `agent.voice` | string | `agent.session` | Voice model used |
| `aoai.session_id` | string | `aoai.realtime.session` | Session ID from Azure OpenAI |
| `gen_ai.usage.input_tokens` | int | `agent.response_turn` | If available from response |
| `gen_ai.usage.output_tokens` | int | `agent.response_turn` | If available from response |

---

## Error Recording Strategy

Errors are recorded using **two mechanisms together**:

1. **Span status** — Set `span.set_status(StatusCode.ERROR, description)` on the span where the error occurred
2. **Error event** — Record the exception as a separate span event via `span.record_exception(exception)`, which automatically captures `exception.type`, `exception.message`, and `exception.stacktrace`

### Error Attribution Rules

| Error Source | Span to Record On | Example |
|---|---|---|
| WebSocket disconnect (unexpected) | `ws.session` | Client drops connection |
| Azure OpenAI Realtime error | `aoai.realtime.session` + `agent.response_turn` | `ListenEvents.ERROR` |
| Tool/function execution failure | `execute_tool` | Plugin raises an exception |
| Handoff failure | `invoke_agent` | Target agent not found |
| Transcription failure | `agent.response_turn` | `TRANSCRIPTION_FAILED` event |

---

## Data Hygiene Rules

This is a **demo/accelerator application**. By default, all fields are **allowed** in trace data, including message content, transcriptions, and tool arguments/results.

### Default: Allow-All

* `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` — captures LLM message content
* `AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true` — captures Azure SDK gen_ai content
* Transcription text, tool arguments, and tool results are recorded as span attributes

### Opt-In Blocking (for production deployments)

When deployers need PII redaction, they can configure the following:

* Set `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=false` to suppress LLM content
* Set `AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=false` to suppress Azure SDK content
* A future `config.yaml` section (`telemetry.redact_fields`) can specify fields to strip from `tool.call.arguments` and `tool.call.results` before setting them as span attributes

### Fields That Must Never Be Redacted

`session.id`, `agent.name`, `tool.name`, `handoff.from`, `handoff.to`, `error.type`, span timing, and span status — these are essential for debugging and contain no PII.

---

## Example Trace Tree in Application Insights

### Typical Call with Handoff

```
ws.session (session.id=a1b2c3, duration=3m42s, service.name=ai-contact-centre)
│
├── aoai.realtime.session (aoai.session_id=sess_xyz, duration=3m40s)
│
├── agent.session (agent.name=triage, duration=1m12s)
│   ├── agent.response_turn (duration=2.3s)
│   ├── execute_tool (tool.name=verify_customer, tool.plugin=CustomerPlugin, duration=850ms)
│   ├── agent.response_turn (duration=1.8s)
│   └── invoke_agent (handoff.from=triage, handoff.to=billing, duration=120ms)
│
├── agent.session (agent.name=billing, duration=2m28s)
│   ├── agent.response_turn (duration=2.1s)
│   ├── execute_tool (tool.name=lookup_balance, tool.plugin=BillingPlugin, duration=340ms)
│   ├── agent.response_turn (duration=1.5s)
│   └── agent.response_turn (duration=1.9s)
│
└── ws.disconnect (duration=15ms)
```

### Query Hints for Application Insights (KQL)

**Find all call sessions:**
```kql
dependencies
| union requests
| where name == "ws.session"
| project session_id = customDimensions["session.id"], timestamp, duration, success
| order by timestamp desc
```

**Find all calls that involved a handoff:**
```kql
dependencies
| where name == "invoke_agent"
| extend session_id = customDimensions["session.id"],
         from_agent = tostring(customDimensions["handoff.from"]),
         to_agent = tostring(customDimensions["handoff.to"])
| project session_id, timestamp, from_agent, to_agent, duration
```

**Find all failed tool calls:**
```kql
dependencies
| where name == "execute_tool"
| where success == false
| extend session_id = customDimensions["session.id"],
         tool = tostring(customDimensions["tool.name"]),
         error = tostring(customDimensions["error.type"])
| project session_id, timestamp, tool, error, duration
```

**Find long-running calls (> 5 minutes):**
```kql
requests
| where name == "ws.session"
| where duration > 5m
| extend session_id = customDimensions["session.id"]
| project session_id, timestamp, duration
| order by duration desc
```

**Find errors in a specific session:**
```kql
dependencies
| union requests, exceptions
| where customDimensions["session.id"] == "a1b2c3"
| where success == false or itemType == "exception"
| project timestamp, name, itemType, customDimensions
| order by timestamp asc
```

---

## Implementation Approach

1. **Configure `TracerProvider`** at app startup in `main.py` using `azure-monitor-opentelemetry` with the Application Insights connection string already output by Terraform
2. **Create root `ws.session` span** in `routes/call.py` at WebSocket accept, close on disconnect
3. **Create `agent.session` spans** in `orchestration.py` when an agent becomes active
4. **Create `invoke_agent` and `execute_tool` spans** using the existing `on_function_call` / `on_function_result` callbacks
5. **Let Semantic Kernel's built-in OTel** handle LLM-level spans automatically once the `TracerProvider` is configured
6. **Set `OTEL_SERVICE_NAME=ai-contact-centre`** in the container/environment configuration

## Pros and Cons of the Options

### Option 1: WebSocket Session as Root Span

* Good, because one trace = one call — intuitive for contact centre debugging
* Good, because the WebSocket lifecycle in `routes/call.py` has clear start/end boundaries
* Good, because all child spans (agents, tools, handoffs) nest naturally under the session
* Good, because Application Insights and Foundry both support long-duration spans
* Bad, because very long calls (30+ minutes) produce large trace trees
* Bad, because if the app crashes, the root span may not be properly closed (mitigated by `TracerProvider.shutdown()` in a `finally` block)

### Option 2: Per-Message Root Spans

* Good, because each span is short and bounded
* Good, because fits standard request/response tracing patterns
* Bad, because correlating a full call requires joining on `session.id` across many independent traces
* Bad, because handoff context is split across traces
* Bad, because Foundry portal's trace view is designed around hierarchical trees, not flat correlated spans
