# Architecture

This document provides detailed technical reference for the AI Contact Centre Solution Accelerator.

> **New to realtime voice AI?** Start with the [README](../README.md) which explains core concepts like
> VoiceLive, handoffs, and Semantic Kernel.

## Overview

The AI Contact Centre Solution Accelerator is a multi-agent voice conversation system built on Azure OpenAI's Realtime
API (or VoiceLive) and Microsoft Semantic Kernel. It enables building intelligent contact centres where specialized AI
agents handle different domains and seamlessly hand off conversations.

**Key architectural decisions:**
- [Why Python?](adrs/2026-01-26-Use-Python.md) - AI/ML ecosystem maturity, Semantic Kernel support
- [Why FastAPI?](adrs/2026-01-26-Use-FastAPI.md) - Async/await, native WebSocket support
- [Why VoiceLive?](adrs/2026-01-27-Use-VoiceLive-with-Noise-Suppression.md) - 89% function call success in noisy environments
- [Why Semantic Kernel?](adrs/2026-01-28-Use-Semantic-Kernel-For-Agentic-Framework.md) - Full feature support for Azure Voice Live + ACS

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            Entry Points                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │  Voice Debugger  │  │    ACS Phone     │  │   Direct WebSocket   │  │
│  │  (Browser UI)    │  │     Calls        │  │      Clients         │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────┬───────────┘  │
└───────────│─────────────────────│────────────────────────│──────────────┘
            │                     │                        │
            │ WebSocket           │ Event Grid +           │ WebSocket
            │ ws://host/ws        │ WebSocket              │
            ▼                     ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                              │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      WebSocket Handler                             │  │
│  │  - Audio routing (base64 PCM16)                                   │  │
│  │  - Event dispatching (Transcription, AgentSwitch, FunctionCall)   │  │
│  │  - ACS media streaming integration                                │  │
│  └────────────────────────────────┬──────────────────────────────────┘  │
│                                   │                                      │
│  ┌────────────────────────────────▼──────────────────────────────────┐  │
│  │                RealtimeHandoffOrchestration                        │  │
│  │  - Agent lifecycle management                                      │  │
│  │  - Handoff function injection (transfer_to_X)                     │  │
│  │  - Silent handoff coordination                                     │  │
│  │  - Function call routing to correct agent                         │  │
│  │  - MCP plugin integration                                          │  │
│  └────────────────────────────────┬──────────────────────────────────┘  │
│                                   │                                      │
│  ┌────────────────────────────────▼──────────────────────────────────┐  │
│  │                        Agent Pool                                  │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │  │
│  │  │  Receptionist   │  │     Billing     │  │    Support      │   │  │
│  │  │  Agent          │  │     Agent       │  │    Agent        │   │  │
│  │  │  - Instructions │  │  - Instructions │  │  - Instructions │   │  │
│  │  │  - Voice        │  │  - Voice        │  │  - Voice        │   │  │
│  │  │  - Plugins      │  │  - Plugins      │  │  - Plugins      │   │  │
│  │  │  - MCP Servers  │  │  - MCP Servers  │  │  - MCP Servers  │   │  │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘   │  │
│  │           │                    │                    │            │  │
│  │           ▼                    ▼                    ▼            │  │
│  │  ┌─────────────────────────────────────────────────────────────┐ │  │
│  │  │                    Semantic Kernel                          │ │  │
│  │  │  - Plugin functions (@kernel_function)                      │ │  │
│  │  │  - MCP server tools (HTTP/stdio)                            │ │  │
│  │  │  - Handoff functions (auto-injected)                        │ │  │
│  │  └─────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────────┐  ┌───────────────────────┐  ┌───────────────────┐
│  Azure OpenAI     │  │    MCP Servers        │  │ Azure Comm.       │
│  Realtime API     │  │                       │  │ Services          │
│  (or VoiceLive)   │  │  ┌───────────────┐   │  │                   │
│                   │  │  │ HTTP Servers  │   │  │ - Phone numbers   │
│  - VAD            │  │  │ (CRM, KB, etc)│   │  │ - Call routing    │
│  - Transcription  │  │  └───────────────┘   │  │ - Event Grid      │
│  - LLM processing │  │  ┌───────────────┐   │  │                   │
│  - TTS response   │  │  │ Stdio Servers │   │  │                   │
│  - Function calls │  │  │ (Local tools) │   │  │                   │
│                   │  │  └───────────────┘   │  │                   │
└───────────────────┘  └───────────────────────┘  └───────────────────┘
```

## Core Components

### 1. Configuration Layer (`config.py`)

The configuration layer manages all settings through `config.yaml`:

- **Environment variable substitution**: `${VAR_NAME}` syntax for secrets
- **Pydantic validation**: Type-safe configuration with clear error messages
- **Cross-field validation**: Validates handoffs, plugins, and MCP servers reference existing definitions
- **Global singleton**: Configuration loaded once at startup

Key configuration sections:

```yaml
app:              # Application metadata
azure_openai:     # Azure OpenAI connection settings
voicelive:        # VoiceLive-specific settings (noise reduction, etc.)
server:           # Host, port, log level
voice:            # Default voice settings
turn_detection:   # VAD configuration
agents:           # Agent definitions
handoffs:         # Agent-to-agent routing
plugins:          # Custom Python tools
mcp_servers:      # External MCP tool servers
orchestration:    # Handoff behavior settings
authentication:   # ACS JWT validation settings
acs:              # Azure Communication Services settings
```

### 2. Agent Layer (`agents/`)

#### RealtimeAgent

A lightweight configuration container for agents:

```python
class RealtimeAgent:
    name: str           # Unique identifier (lowercase, underscores)
    description: str    # Used in handoff descriptions
    instructions: str   # System prompt
    voice: str          # TTS voice name
    kernel: Kernel      # Semantic Kernel with plugins
    plugins: list       # Assigned plugin instances
```

#### Agent Factory

Creates agents and handoffs from configuration at the start of a call:

```python
agents = create_agents(config)      # Dict[str, RealtimeAgent]
handoffs = create_handoffs(agents, config)  # OrchestrationHandoffs
```

### 3. Plugin Layer (`tools/`)

Two types of tools are supported:

#### Custom Plugins (Python)

Plugins are Python classes with `@kernel_function` decorated methods:

```python
from semantic_kernel.functions import kernel_function

class BillingPlugin:
    """Plugin with billing-related functions."""
    
    @kernel_function(description="Get account balance")
    def get_balance(self, account_id: str) -> str:
        return f"Balance for {account_id}: $100.00"
```

Plugin configuration:
```yaml
plugins:
  - name: "billing_plugin"
    module: "example_tools"    # Module in src/tools/
    class_name: "BillingPlugin"
```

#### MCP Servers (External)

External tools via Model Context Protocol:

```yaml
mcp_servers:
  # HTTP transport - remote servers
  - name: "crm"
    transport: "http"
    url: "https://crm.example.com/mcp"
    headers:
      Authorization: "Bearer ${CRM_API_KEY}"
  
  # Stdio transport - local processes
  - name: "knowledge_base"
    transport: "stdio"
    command: "npx"
    args: ["-y", "@company/kb-mcp-server"]
```

MCP servers are started at application startup (`mcp_loader.py`) and stopped at shutdown.

### 4. Orchestration Layer (`core/orchestration.py`)

The `RealtimeHandoffOrchestration` manages multi-agent conversations:

**Key responsibilities:**
1. **Session management**: Single shared realtime session per call
2. **Agent switching**: Updates session with new agent context, instructions, and tools
3. **Handoff injection**: Dynamically adds `transfer_to_X` functions to each agent's kernel
4. **Silent handoffs**: Transfers without announcing to user (configurable)
5. **Function routing**: Routes function calls to the correct agent's tools
6. **MCP integration**: Adds MCP plugins after kernel cloning

**Handoff flow:**
```
User: "I have a billing question"
       │
       ▼
┌──────────────────┐
│   Receptionist   │ ──▶ Detects billing intent
└──────────────────┘
       │
       │ Calls transfer_to_billing()
       ▼
┌──────────────────┐
│ Orchestration    │ ──▶ Updates session with billing agent
└──────────────────┘     (instructions, voice, tools)
       │
       ▼
┌──────────────────┐
│     Billing      │ ──▶ Responds with billing-specific voice
└──────────────────┘
```

### 5. Voice Processing

#### Client Types

The accelerator supports two Azure OpenAI client types:

**VoiceLive** (default):
- Enhanced audio processing (noise reduction, echo cancellation)
- Semantic VAD option
- Azure TTS voices (e.g., `en-US-AvaMultilingualNeural`)
- Viseme animation support

**Realtime**:
- Direct OpenAI Realtime API
- OpenAI voices (alloy, echo, fable, onyx, nova, shimmer)
- Server VAD

Configuration:
```yaml
azure_openai:
  client_type: "voicelive"  # or "realtime"
```

### 6. WebSocket Handler (`routes/call.py`)

Manages real-time voice communication:

- **Audio routing**: Bidirectional audio between client and Azure OpenAI
- **Event handling**: Transcriptions, agent switches, function calls, errors
- **State management**: Current agent tracking, chat history
- **Protocol translation**: Converts between client format and Azure format

WebSocket message types:
```json
{"kind": "AudioData", "audioData": {"data": "<base64 PCM16>"}}
{"kind": "Transcription", "data": {"speaker": "user", "text": "..."}}
{"kind": "AgentSwitch", "data": {"agentName": "billing"}}
{"kind": "FunctionCall", "data": {"plugin": "...", "function": "...", "arguments": "..."}}
{"kind": "FunctionResult", "data": {"plugin": "...", "function": "...", "result": "..."}}
```

### 7. ACS Integration (`routes/incoming.py`)

Handles Azure Communication Services phone calls:

**Incoming Call Flow:**
1. Event Grid sends `AcsIncomingCallEvent` to `/calls/incoming`
2. Application answers call with media streaming options
3. ACS connects to `/ws` WebSocket endpoint
4. Audio flows bidirectionally between phone and AI agents

**Configuration:**

ACS configuration is loaded automatically from environment variables:
- `ACS_CONNECTION_STRING`: Connection string from Azure Communication Services
- `CONTAINER_APP_HOSTNAME`: Automatically injected by Azure Container Apps (or set `ACS_CALLBACK_HOST` for local dev)

```yaml
authentication:
  enabled: true
  acs_resource_id: "your-resource-id"
```

## Data Flow

### Voice Input Flow

```
1. Client captures audio (24kHz PCM16 mono)
2. Audio encoded as base64 and sent via WebSocket
3. FastAPI receives and forwards to orchestration
4. Orchestration sends to Azure OpenAI (Realtime/VoiceLive)
5. Azure performs:
   - Voice activity detection (VAD)
   - Speech-to-text transcription
   - LLM processing with agent instructions
   - Function calling (routed through orchestration)
   - Text-to-speech response generation
6. Audio response streamed back through same path
```

### Handoff Flow

```
1. Current agent detects need for handoff (or model decides)
2. Agent calls transfer_to_X function (injected by orchestration)
3. Orchestration marks handoff as pending
4. After function result, orchestration:
   a. Updates session with new agent's instructions
   b. Updates session with new agent's tools
   c. Changes voice if configured differently
   d. Emits AgentSwitch event to client
5. New agent continues conversation seamlessly
```

### Function Call Flow

```
1. Azure OpenAI decides to call a function
2. Orchestration receives function call event
3. Orchestration routes to correct plugin:
   - Custom plugin: Direct method invocation
   - MCP server: Protocol call to external server
   - Handoff function: Triggers agent switch
4. Result returned to Azure OpenAI
5. Model incorporates result into response
```

## Configuration Schema

### Complete config.yaml Structure

```yaml
# Application metadata
app:
  name: string
  description: string
  version: string

# Azure OpenAI settings
azure_openai:
  endpoint: string           # ${AZURE_OPENAI_ENDPOINT}
  deployment: string         # gpt-4o-realtime
  api_version: string
  transcription_model: string
  client_type: string        # "realtime" or "voicelive"

# VoiceLive-specific settings
voicelive:
  noise_reduction:
    enabled: boolean
  echo_cancellation:
    enabled: boolean
  semantic_vad:
    enabled: boolean
    eagerness: string        # low, medium, high, auto
  voice:
    type: string             # azure-standard, azure-custom
    rate: string
    temperature: float

# Server settings
server:
  host: string
  port: integer
  log_level: string

# Voice settings
voice:
  default: string            # Voice name (Azure TTS or OpenAI)

# VAD settings
turn_detection:
  type: string               # server_vad
  silence_duration_ms: integer
  threshold: float
  create_response: boolean

# Agent definitions
agents:
  - name: string             # lowercase, underscores only
    description: string      # required, used in handoffs
    voice: string            # optional, overrides default
    instructions: string
    plugins: [string]        # list of plugin names
    mcp_servers: [string]    # list of MCP server names

# Handoff definitions
handoffs:
  - from: string             # source agent name
    to: string               # target agent name
    description: string      # when to trigger

# Plugin definitions
plugins:
  - name: string             # plugin name
    module: string           # Python module in tools/
    class_name: string       # Class name
    description: string

# MCP Server definitions
mcp_servers:
  - name: string             # server name
    transport: string        # "http" or "stdio"
    enabled: boolean         # default: true
    # HTTP transport
    url: string
    headers: map[string]string
    # Stdio transport
    command: string
    args: [string]
    env: map[string]string

# Orchestration settings
orchestration:
  silent_handoffs: boolean

# ACS settings (loaded from environment variables)
# - ACS_CONNECTION_STRING: Connection string from Azure Communication Services
# - CONTAINER_APP_HOSTNAME: Auto-injected by Container Apps (or ACS_CALLBACK_HOST for local dev)

# Authentication settings
authentication:
  enabled: boolean
  acs_resource_id: string
  jwks_cache_lifespan: integer
```

## Evaluation Module

The `eval/` directory contains an automated evaluation system:

```
eval/
├── src/eval/
│   ├── conversation_simulator.py  # Runs scenarios
│   ├── customer.py                # LLM-driven customer
│   ├── transport.py               # WebSocket client
│   ├── voice.py                   # TTS/transcription
│   ├── runner.py                  # Orchestrates evaluation
│   └── evaluators/
│       └── function_call.py       # Custom evaluator
├── scenarios.jsonl                # Test scenarios
└── config.yaml                    # Eval configuration
```

**Evaluation Flow:**
1. Load scenarios from JSONL
2. For each scenario:
   - Connect to accelerator WebSocket
   - Wait for agent greeting
   - LLM generates customer responses based on scenario instructions
   - TTS converts to audio, sends to accelerator
   - Transcribe agent responses
   - Collect function calls and agent switches
3. Run evaluators:
   - Function call precision/recall/F1
   - Intent resolution (Azure AI SDK)
   - Coherence (Azure AI SDK)
4. Output results to JSON/CSV

## Security Considerations

1. **Authentication**: Uses Azure DefaultAzureCredential (CLI, managed identity, service principal)
2. **No secrets in config**: Use `${VAR_NAME}` environment variable substitution
3. **ACS JWT validation**: Optional JWT authentication for WebSocket connections
4. **Input validation**: Pydantic validates all configuration
5. **Non-root Docker**: Container runs as unprivileged user

## Performance Considerations

1. **Single WebSocket per call**: Each call gets its own Azure OpenAI connection
2. **Startup initialization**: Agents, plugins, and MCP servers loaded once at startup
3. **Shared agent definitions**: Agents created once, kernels cloned per session
4. **Async throughout**: Non-blocking I/O operations
5. **MCP connection reuse**: MCP servers stay connected across calls

## Extension Points

1. **Custom plugins**: Add Python modules to `tools/` with `@kernel_function` methods
2. **MCP servers**: Connect external tools via HTTP or stdio
3. **Custom agents**: Define in `config.yaml` with instructions and tool assignments
4. **Custom handoffs**: Define routing rules in `config.yaml`
5. **Middleware**: Add FastAPI middleware for logging, auth, etc.
6. **Evaluators**: Add custom evaluators in `eval/src/eval/evaluators/`
7. **Voice customization**: Configure VoiceLive settings or use custom Azure voices

## Glossary

| Term | Definition |
|------|------------|
| **Agent** | An AI persona with specific instructions, voice, and tools. Each agent handles a domain (billing, support, etc.) |
| **ASGI** | Asynchronous Server Gateway Interface - the Python standard for async web servers |
| **DefaultAzureCredential** | Azure SDK class that automatically selects the best authentication method (CLI, managed identity, etc.) |
| **Handoff** | Transferring a conversation from one agent to another while preserving context |
| **Kernel** | Semantic Kernel's core orchestration object that manages plugins and AI connections |
| **MCP** | Model Context Protocol - open standard for connecting AI models to external tools |
| **PCM16** | Pulse Code Modulation, 16-bit - audio format using signed 16-bit integers per sample |
| **Plugin** | A Python class with `@kernel_function` methods that the AI can call |
| **Realtime API** | Azure OpenAI's streaming voice conversation API with basic audio processing |
| **Semantic Kernel** | Microsoft's AI orchestration framework for building AI applications |
| **Silent Handoff** | Agent transfer that happens without announcing to the user ("please hold") |
| **VAD** | Voice Activity Detection - determining when someone is speaking vs silent |
| **VoiceLive** | Enhanced Realtime API with noise reduction, echo cancellation, and semantic VAD |
| **WebSocket** | Protocol for bidirectional real-time communication over a single TCP connection |

## Further Reading

- [Architecture Decision Records](adrs/README.md) - Why we made specific technical choices
- [Evaluation Guide](../eval/README.md) - Automated testing documentation
- [Azure OpenAI Realtime API](https://learn.microsoft.com/en-us/azure/ai-services/openai/realtime-audio-reference)
- [Azure Voice Live](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live)
- [Semantic Kernel Documentation](https://learn.microsoft.com/en-us/semantic-kernel/)
