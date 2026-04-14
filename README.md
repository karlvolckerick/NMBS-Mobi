# NMBS AI Contact Centre

> Built on the [AI Contact Centre Solution Accelerator](https://github.com/Azure-Samples/ai-contact-centre-solution-accelerator) — a production-ready, multi-agent realtime voice assistant using Azure AI Services and Semantic Kernel.

An AI-powered contact centre for **NMBS (Belgian Railways)** — callers speak naturally with AI agents that handle train enquiries, ticketing, disruptions, and digital support across 4 languages (EN/NL/FR/DE). No IVR menus. No hold queues.

## 📞 Live Deployment

| | |
|---|---|
| **Phone number** | **+1 (866) 493-9541** (US toll-free) |
| **App URL** | https://ai-contact-centre-app.graysea-a080a32a.swedencentral.azurecontainerapps.io |
| **Health check** | [`/status`](https://ai-contact-centre-app.graysea-a080a32a.swedencentral.azurecontainerapps.io/status) |
| **Region** | Sweden Central |
| **Resource group** | `rg-ai-contact-centre-7rqtlr` |

## 🤖 AI Agents

| Agent | Voice | Handles |
|---|---|---|
| **Receptionist** | en-US-AvaMultilingualNeural | Greeting, language selection (EN/NL/FR/DE), journey planning, live departures & connections |
| **Ticketing** | en-US-AvaMultilingualNeural | Ticket purchases, Rail Pass, seat reservations, refunds, fare questions |
| **Disruptions** | en-US-AndrewMultilingualNeural | Live delays, cancellations, alternative routes, missed connections, delay compensation |
| **Digital Support** | en-US-AvaMultilingualNeural | NMBS app issues, QR ticket scanning, login problems, payment errors |

Agents hand off silently — callers hear no "please hold" message, just the new agent continuing the conversation.

## 🎯 Features

- **Multi-Agent Orchestration**: 4 specialist agents with intelligent silent handoffs
- **Realtime Voice Processing**: Azure OpenAI VoiceLive with deep noise suppression (89% function call success rate)
- **Live iRail Train Data**: Real-time departures, connections, disruptions via the open iRail API
- **Multilingual**: EN / NL / FR / DE — language selected by the caller at the start of each call
- **Email Follow-up**: All agents can send callers timetables, ticket confirmations, or disruption summaries via email
- **ACS Phone Integration**: Real inbound calls via Azure Communication Services
- **YAML Configuration**: Agents, tools, and handoffs defined without code changes
- **MCP Server Support**: Email sender via Model Context Protocol (stdio)
- **Infrastructure as Code**: Terraform deploys all Azure resources
- **Docker Ready**: Production container deployed to Azure Container Apps

## 💡 Key Concepts

New to realtime voice AI? This section explains the core concepts.

### What is Realtime Voice AI?

Traditional chatbots work with text: you type, wait, get a response. **Realtime voice AI** is different - it
processes spoken audio continuously, like a phone call:

1. **Listens continuously** - No "press to talk" button
2. **Detects when you stop speaking** - Voice Activity Detection (VAD) identifies natural pauses
3. **Processes speech immediately** - Transcription and AI response happen in real-time
4. **Responds with synthesized speech** - Text-to-speech generates natural voice responses

This creates fluid, conversational interactions - ideal for contact centres where customers expect to speak
naturally.

### VoiceLive vs Realtime API

The accelerator supports two Azure OpenAI client types:

| Feature           | Realtime API       | VoiceLive                               |
|-------------------|--------------------|-----------------------------------------|
| Noise reduction   | Basic              | Advanced (azure_deep_noise_suppression) |
| Echo cancellation | No                 | Yes                                     |
| Best for          | Quiet environments | Real-world conditions (offices, cafes)  |
| Voices            | 6 OpenAI voices    | 600+ Azure TTS voices                   |

**We recommend VoiceLive for production** - it achieves 89% function call success rate across noise conditions
vs 82% for Realtime API.
See [ADR: VoiceLive with Noise Suppression](docs/adrs/2026-01-27-Use-VoiceLive-with-Noise-Suppression.md)
for the experimental data behind this decision.

### Multi-Agent Handoffs

In a contact centre, different specialists handle different requests. A **handoff** transfers the conversation
from one AI agent to another:

```
Caller dials +1 866 493 9541
→ Receptionist greets in EN/NL/FR/DE
Caller: "I want to claim compensation for a delayed train"
→ Receptionist silently hands off to Disruptions agent
Disruptions agent: "I can help with that. Which train were you on?"
```

The transfer is **silent** - the caller hears the new agent's voice but no "please hold" message. The new
agent receives the full conversation history.

### Semantic Kernel

[Semantic Kernel](https://github.com/microsoft/semantic-kernel) is Microsoft's AI orchestration framework. It
manages connecting to Azure AI Services, calling functions when the AI needs data, and routing requests to the right
agent.

You don't need to understand Semantic Kernel internals - the accelerator abstracts this complexity. See
[ADR: Semantic Kernel as Agentic Framework](docs/adrs/2026-01-28-Use-Semantic-Kernel-For-Agentic-Framework.md)
for why we chose it over alternatives like LangChain and LiveKit.

### Model Context Protocol (MCP)

MCP is an open standard for connecting AI models to external tools. Instead of writing custom integrations, you
can connect to any MCP-compatible server (CRMs, databases, APIs) with simple configuration. The accelerator
supports both HTTP and stdio transports.

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│         Caller dials +1 (866) 493-9541 (ACS toll-free)          │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│          Azure Communication Services (ACS)                      │
│          Phone number · Call routing · Audio stream              │
└─────────────────────────┬────────────────────────────────────────┘
                          │ Event Grid + WebSocket
                          ▼
┌────────────────────────────────────────────────────────────────┐
│           FastAPI Application (Azure Container Apps)           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              RealtimeHandoffOrchestration                │   │
│  │  ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐  │   │
│  │  │Receptionist│ │Ticketing │ │Disruptions│ │ Digital  │  │   │
│  │  │+ iRail    │ │+ Billing │ │+ iRail    │  │ Support  │  │   │
│  │  │+ Email MCP│ │+ Email   │ │+ Email    │ │+ Email   │  │   │
│  │  └───────────┘ └──────────┘ └───────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────┬──────────────────────┬───────────────────────────────┘
           │                      │
           ▼                      ▼
┌──────────────────────┐  ┌──────────────────────┐
│  Azure OpenAI        │  │  iRail Open API       │
│  VoiceLive           │  │  api.irail.be         │
│  - Deep noise supp.  │  │  - Live departures    │
│  - Echo cancellation │  │  - Connections        │
│  - 600+ TTS voices   │  │  - Disruptions        │
│  - Semantic VAD      │  └──────────────────────┘
└──────────────────────┘
```

**Azure services used:**

| Service | Purpose |
|---|---|
| Azure OpenAI (VoiceLive) | Voice AI — STT + LLM + TTS in one API |
| Azure Communication Services | Phone number + call routing |
| Azure Container Apps | Hosts the FastAPI application (Sweden Central) |
| Azure Container Registry | Stores the Docker image |
| Azure Event Grid | Delivers inbound call events to the app |
| Azure Application Insights | Monitoring & telemetry |
| Managed Identity | Passwordless auth between all services |

See [Architecture Guide](docs/architecture.md) for detailed component documentation.

## 🚀 Quick Start

> **🤖 Prefer AI-assisted setup?** This project has built-in [GitHub Copilot skills](docs/copilot.md) that can
> walk you through setup, deployment, configuration, and more — interactively. Open the Copilot Chat panel in VS Code,
> select **Agent mode**, and ask *"Help me get this running locally"*. Copilot will detect your current state, install
> dependencies, deploy infrastructure, and start the app — all through conversation.

Follow these steps to get the accelerator running locally.

### Prerequisites

Before starting, ensure you have these tools installed:

| Tool      | Version | Installation                                                                       |
|-----------|---------|------------------------------------------------------------------------------------|
| Python    | 3.12+   | [python.org](https://www.python.org/downloads/)                                    |
| uv        | Latest  | [docs.astral.sh/uv](https://docs.astral.sh/uv/)                                    |
| Task      | Latest  | [taskfile.dev](https://taskfile.dev/installation/)                                 |
| Terraform | 1.0+    | [terraform.io](https://www.terraform.io/downloads)                                 |
| Azure CLI | Latest  | [docs.microsoft.com](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) |

After installing Azure CLI, add the Container Apps extension:

```bash
az extension add -n containerapp
```

**Azure Requirements:**

- Azure subscription with **Contributor** access
- Azure AI Services access with OpenAI models ([request access](https://aka.ms/oai/access) - approval typically takes 1-2 business
  days)

> **Note**: You do NOT need to manually create Azure AI Services, Container Registry, or other resources.
> The Terraform modules in `infra/` deploy everything automatically.

### Step 1: Clone and Install

```bash
git clone <repository-url>
cd ai-contact-centre-solution-accelerator

# Create virtual environment and install dependencies
task deps
```

**Expected output**: Virtual environment created in `.venv/`, all dependencies installed.

### Step 2: Authenticate with Azure

```bash
az login
az account set --subscription "YOUR-SUBSCRIPTION-NAME"
```

The accelerator uses `DefaultAzureCredential`, which automatically uses your Azure CLI credentials locally and
managed identity in production.

### Step 3: Deploy Azure Infrastructure

The Terraform modules deploy all required Azure resources:

```bash
# Copy the example configuration
cp infra/terraform.tfvars.example infra/terraform.tfvars
```

Edit `infra/terraform.tfvars`:

```hcl
project_name    = "my-contact-centre"
subscription_id = "your-subscription-id"  # Get with: az account show --query id -o tsv
location        = "swedencentral"         # Region with Realtime model support
```

> **Important**: Choose a region with Azure AI Services Realtime model availability. As of January 2026,
> **Sweden Central** and **East US 2** have full support. Check
> [Azure AI Services model availability](https://learn.microsoft.com/azure/ai-services/openai/concepts/models)
> for current status.

Deploy the infrastructure:

```bash
task tf-init    # Initialize Terraform
task tf-plan    # Preview changes (review before applying)
task tf-apply   # Deploy (type 'yes' to confirm)
```

**What gets deployed:**
| Resource | Purpose |
|----------|---------|
| Azure AI Services account | Hosts the AI models |
| gpt-realtime deployment | Realtime voice conversations |
| gpt-4o-transcribe deployment | Speech-to-text for evaluation |
| gpt-4.1 deployment | Customer simulation in evaluation |
| tts deployment | Text-to-speech for evaluation |
| Container Registry | Stores Docker images for production |
| Container App Environment | Hosts the application in production |

### Step 4: Run the Application

```bash
task run
```

This automatically reads the Azure AI Services endpoint from Terraform output and starts the server.

**Expected output**:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 5: Test the Voice Debugger

1. Open http://localhost:8000 in your browser
2. Click the microphone button to enable audio
3. Say "Hello" - the receptionist agent should greet you
4. Try "I have a billing question" to test handoffs

**Success criteria:**

- [ ] Application starts without errors
- [ ] Voice debugger UI loads in browser
- [ ] Agent responds to voice input
- [ ] Saying "billing" triggers a handoff to the billing agent

## 🔧 Configuration Guide

All configuration is managed through `config.yaml`. The accelerator uses Pydantic for validation and supports
environment variable substitution with `${VAR_NAME}` syntax.

### Defining Agents

Each agent has a unique name, description, voice, instructions, and assigned tools:

```yaml
agents:
  - name: "receptionist"
    description: "Routes callers to the appropriate department"
    voice: "en-US-AvaMultilingualNeural"  # Azure TTS voice
    instructions: |
      You are a receptionist for Acme Corp.
      Route callers to billing or support as needed.
    plugins:
      - "receptionist_plugin"
    mcp_servers:
      - "crm_server"  # Optional: MCP server tools

  - name: "billing"
    description: "Handles billing and payment questions"
    voice: "en-GB-SoniaNeural"
    instructions: |
      You are a billing specialist.
      Help customers with payment questions.
    plugins:
      - "billing_plugin"
```

**Agent fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier (lowercase, underscores) |
| `description` | Yes | Used in handoff function descriptions |
| `instructions` | Yes | System prompt defining agent behavior |
| `voice` | No | TTS voice (defaults to `voice.default`) |
| `plugins` | No | List of plugin names to assign |
| `mcp` | No | List of MCP server names to assign |

### Defining Handoffs

Handoffs define which agents can transfer to which other agents:

```yaml
handoffs:
  - from: "receptionist"
    to: "billing"
    description: "Transfer for billing questions"

  - from: "receptionist"
    to: "support"
    description: "Transfer for technical issues"

  - from: "billing"
    to: "receptionist"
    description: "Transfer for general questions"
```

The orchestration layer automatically injects `transfer_to_X` functions into each agent based on these definitions.

### Defining Plugins (Custom Tools)

Plugins are Python classes with `@kernel_function` decorated methods:

```yaml
plugins:
  - name: "billing_plugin"
    module: "example_tools"      # Module in src/tools/
    class_name: "BillingPlugin"  # Class name
    description: "Billing functions"
```

### Defining MCP Servers (External Tools)

Connect to external tool servers via Model Context Protocol:

```yaml
mcp_servers:
  # HTTP transport - remote servers
  - name: "crm"
    transport: "http"
    url: "https://crm.example.com/mcp"
    headers:
      Authorization: "Bearer ${CRM_API_KEY}"

  # Stdio transport - local process
  - name: "knowledge_base"
    transport: "stdio"
    command: "npx"
    args: [ "-y", "@company/kb-mcp-server" ]
    env:
      API_KEY: "${KB_API_KEY}"
```

### Voice Configuration

**VoiceLive** (recommended):

```yaml
azure_openai:
  client_type: "voicelive"

voicelive:
  noise_reduction:
    enabled: true
  echo_cancellation:
    enabled: true

voice:
  default: "en-US-AvaMultilingualNeural"  # Azure TTS voice
```

**Realtime API**:

```yaml
azure_openai:
  client_type: "realtime"

voice:
  default: "alloy"  # OpenAI voices: alloy, echo, fable, onyx, nova, shimmer
```

See [ADR: VoiceLive](docs/adrs/2026-01-27-Use-VoiceLive-with-Noise-Suppression.md) for guidance on when to use each.

### Orchestration Settings

```yaml
orchestration:
  silent_handoffs: true  # Agents transfer without announcing
```

## 🛠️ Creating Custom Tools

1. **Create a plugin class** in `src/ai_contact_centre_solution_accelerator/tools/`:

```python
# tools/my_tools.py
from semantic_kernel.functions import kernel_function


class MyPlugin:
    """Plugin with custom functions."""

    @kernel_function(description="Look up customer information")
    def lookup_customer(self, customer_id: str) -> str:
        # Your implementation here
        return f"Customer {customer_id}: John Doe"

    @kernel_function(description="Create a support ticket")
    def create_ticket(self, description: str, priority: str = "normal") -> str:
        # Your implementation here
        return f"Ticket created: {description} (Priority: {priority})"
```

2. **Register in config.yaml**:

```yaml
plugins:
  - name: "my_plugin"
    module: "my_tools"
    class_name: "MyPlugin"

agents:
  - name: "support"
    plugins:
      - "my_plugin"
```

The `description` in `@kernel_function` is crucial - it tells the AI when to call the function.

## 🧪 Testing

```bash
# Run all tests (main app + eval module)
task test-all

# Run only main app tests
task test
```

## 📊 Evaluation Module

The accelerator includes an automated evaluation system for testing voice conversations end-to-end.

**What it does:**

1. Connects to the accelerator via WebSocket
2. Simulates customers using an LLM that follows scenario instructions
3. Converts customer text to speech and sends to the accelerator
4. Transcribes agent responses
5. Evaluates function calls, intent resolution, and conversation coherence

See [eval/README.md](eval/README.md) for detailed evaluation documentation.

## 🐳 Docker Deployment

### Local Docker

```bash
task docker-build
task docker-run
```

### Azure Container Apps

The full deployment workflow:

```bash
task deploy  # Runs: tf-init → tf-plan → tf-apply → acr-push → app-up
```

Or step by step:

```bash
task tf-init   # Initialize Terraform
task tf-plan   # Preview infrastructure changes
task tf-apply  # Deploy infrastructure
task acr-push  # Build and push Docker image
task app-up    # Deploy to Container Apps
```

## 📞 Azure Communication Services Integration

To accept real phone calls via ACS, complete the Docker deployment first (see above), then follow these steps:

### Step 1: Ensure Application is Deployed

Make sure you've completed the Docker deployment:

```bash
task deploy  # Deploys infrastructure, builds image, and deploys app
```

### Step 2: Purchase a Phone Number

```bash
task acs-phone-purchase
```

This purchases a UK toll-free number by default. See [Infrastructure Scripts](infra/scripts/README.md) for options.

### Step 3: Configure Event Grid (Automated)

Automatically configure the Event Grid webhook:

```bash
task acs-event-grid-setup  # Updates terraform.tfvars with Container App URL
task tf-plan               # Review Event Grid changes
task tf-apply              # Create Event Grid subscription
```

This creates an Event Grid subscription that routes incoming calls to your application.

### Step 4: Authentication

JWT authentication is enabled automatically by `task app-up` — it sets `ACS_AUTH_ENABLED` and pulls the ACS resource ID
from Terraform. No manual configuration needed.

> **Note**: Authentication is disabled by default when running locally (`task run`) so you can use the voice debugger
> during development. When auth is enabled, the voice debugger UI cannot connect - use the provisioned ACS phone number
> to test instead.

See [ADR: Secure WebSocket Connection](docs/adrs/2026-01-27-Secure-WebSocket-Connection.md) for security details.

## 🏠 Local ACS Debugging

Test real phone calls via Azure Communication Services while running the application locally using Azure Dev Tunnels.
This workflow allows you to debug ACS phone call flows on your development machine without deploying to Azure Container Apps.

### Prerequisites

- Azure infrastructure deployed (`task deploy` or at minimum `task tf-apply`)
- Azure Communication Services phone number purchased (`task acs-phone-purchase`)
- No existing Event Grid subscription (check `infra/terraform.tfvars` — `acs_webhook_endpoint` should be empty or unset)
- Dev tunnel CLI installed (automatically installed in the devcontainer)

### How It Works

The dev tunnel creates a public HTTPS/WSS endpoint that forwards traffic to `localhost:8000`. When ACS receives
an incoming call, Event Grid routes the notification to the tunnel, which forwards it to your local application.
The ACS media streaming WebSocket also connects through the tunnel.

```
Phone Call → ACS → Event Grid → Dev Tunnel → localhost:8000
```

### Workflow

Open **3 terminals** for the development workflow:

**Terminal 1 — Dev Tunnel** (blocks — keeps the tunnel alive):

```bash
task tunnel-up
```

This starts a dev tunnel on port 8000. The first time you run this, it will prompt you to login with a device code.
Keep this terminal open while debugging. The tunnel URL will be displayed in the output.

**Terminal 2 — Application** (blocks — runs the app):

```bash
task run-with-acs
```

This starts the FastAPI app with:
- All required ACS environment variables (connection string, auth settings)
- Tunnel URL as the callback host
- Authentication enabled (required for ACS phone calls)

> **Note**: The voice debugger UI at http://localhost:8000 will NOT work when authentication is enabled. You must
> use the provisioned ACS phone number to test.

**Terminal 3 — Event Grid Setup** (one-shot — creates subscription):

```bash
task acs-local-setup
```

This creates an Event Grid subscription named `local-dev-incoming-call` that routes ACS incoming calls to your
dev tunnel. The task performs these checks before creating the subscription:

1. Verifies an active dev tunnel exists
2. Checks for conflicting Terraform-managed Event Grid subscriptions
3. Performs a health check via the tunnel to ensure the app is reachable
4. Creates the Event Grid subscription

Once complete, call your ACS phone number to test. The call will route to your local application.

### Teardown

When you're done debugging, tear down in this order:

**Terminal 3 — Delete Event Grid subscription**:

```bash
task acs-local-teardown
```

This removes the `local-dev-incoming-call` Event Grid subscription. Safe to run multiple times (idempotent).

**Terminal 2 — Stop application**:

Press `Ctrl+C` to stop the FastAPI app.

**Terminal 1 — Stop tunnel**:

Press `Ctrl+C` to stop the dev tunnel, or in Terminal 3:

```bash
task tunnel-down  # Alternative cleanup — deletes all tunnels
```

## �🔑 Environment Variables

### Core Application

The application reads most settings from `config.yaml`. Environment variables are used for secrets and overrides:

### Azure Communication Services

| Variable                  | Required        | Description                                                         |
|---------------------------|-----------------|---------------------------------------------------------------------|
| `ACS_CONNECTION_STRING`   | For phone calls | ACS connection string (auto-set by `app-up`)                       |
| `CONTAINER_APP_HOSTNAME`  | For callbacks   | Callback hostname for ACS (auto-injected in Container Apps, set manually for local dev) |
| `ACS_AUTH_ENABLED`        | For phone calls | Enable JWT auth on the WebSocket endpoint (auto-set by `app-up`)   |
| `ACS_AUTH_ACS_RESOURCE_ID`| For phone calls | ACS resource ID used as the JWT audience claim (auto-set by `app-up`) |

### MCP Server Secrets

Reference environment variables in `config.yaml` using `${VAR_NAME}` syntax:

```yaml
mcp_servers:
  - name: "crm"
    headers:
      Authorization: "Bearer ${CRM_API_KEY}"  # Reads CRM_API_KEY env var
```

## 📋 Available Tasks

```bash
task --list  # Show all available tasks
```

| Task                      | Description                                         |
|---------------------------|-----------------------------------------------------|
| `task deps`               | Create virtual environment and install dependencies |
| `task run`                | Start the application locally                       |
| `task test`               | Run all tests                                       |
| `task lint`               | Run linter and fix issues                           |
| `task deploy`             | Full deployment workflow                            |
| `task acs-phone-purchase` | Purchase a phone number for ACS                     |
| `task tunnel-up`          | Start dev tunnel for local ACS debugging            |
| `task tunnel-down`        | Clean up all dev tunnels                            |
| `task run-with-acs`       | Start app with ACS environment variables            |
| `task acs-local-setup`    | Create Event Grid subscription for local debugging  |
| `task acs-local-teardown` | Delete local Event Grid subscription                |

## 📚 API Endpoints

| Endpoint                  | Method    | Description                              |
|---------------------------|-----------|------------------------------------------|
| `/`                       | GET       | Voice debugger UI                        |
| `/status`                 | GET       | Health check                             |
| `/config`                 | GET       | Current configuration (secrets redacted) |
| `/ws`                     | WebSocket | Voice conversation endpoint              |
| `/calls/incoming`         | POST      | ACS incoming call webhook                |
| `/calls/events/{call_id}` | POST      | ACS call events webhook                  |

> **Note:** The voice debugger UI (`/`) only works when authentication is disabled (`ACS_AUTH_ENABLED=false`). When auth
> is enabled, the debugger cannot connect because it lacks ACS JWT tokens. Use the provisioned ACS phone number to test
> in authenticated environments.

## 📁 Project Structure

```
├── src/ai_contact_centre_solution_accelerator/
│   ├── agents/          # Agent definitions and factory
│   ├── auth/            # ACS JWT authentication
│   ├── core/            # Orchestration, MCP loader
│   ├── routes/          # API endpoints
│   └── tools/           # Example plugins
├── eval/                # Evaluation module
│   ├── src/eval/        # Evaluation code
│   ├── scenarios.jsonl  # Test scenarios
│   └── config.yaml      # Eval configuration
├── infra/               # Terraform infrastructure
│   └── modules/         # Azure resource modules
├── docs/                # Documentation
│   └── adrs/            # Architecture Decision Records
├── config.yaml          # Main application configuration
└── Taskfile.yaml        # Task automation
```

## 📖 Documentation

- [Architecture Guide](docs/architecture.md) - Detailed system architecture and component reference
- [Copilot Integration](docs/copilot.md) - Skills and workflows for AI-assisted development
- [Evaluation Guide](eval/README.md) - Automated testing documentation
- [Infrastructure Scripts](infra/scripts/README.md) - One-time setup scripts (phone number purchase, etc.)
- [Architecture Decision Records](docs/adrs/README.md) - Design decisions and rationale
    - [Why Python?](docs/adrs/2026-01-26-Use-Python.md)
    - [Why FastAPI?](docs/adrs/2026-01-26-Use-FastAPI.md)
    - [Why VoiceLive?](docs/adrs/2026-01-27-Use-VoiceLive-with-Noise-Suppression.md)
    - [Why Semantic Kernel?](docs/adrs/2026-01-28-Use-Semantic-Kernel-For-Agentic-Framework.md)
    - [WebSocket Authentication](docs/adrs/2026-01-27-Secure-WebSocket-Connection.md)

## 🔧 Troubleshooting

### Application Won't Start

**Error: `AZURE_OPENAI_ENDPOINT not configured` or similar**

- Ensure `config.yaml` has the correct endpoint from `terraform output openai_endpoint`
- Verify the endpoint URL format: `https://YOUR-RESOURCE.cognitiveservices.azure.com/`

**Error: `Model deployment not found`**

- Verify `deployment` name in `config.yaml` matches your Azure AI Services deployment
- Check the deployment is active in Azure AI Studio

**Error: `DefaultAzureCredential failed`**

- Run `az login` to authenticate
- Ensure your account has access to the Azure AI Services resource

### WebSocket Connection Fails

**Browser shows "WebSocket connection failed"**

- Ensure the server is running (`task run`)
- Check browser console for CORS errors
- Use `ws://` (not `wss://`) for local development

**ACS calls don't connect**

- Verify Event Grid subscription points to your public URL
- Check `CONTAINER_APP_HOSTNAME` is set correctly (automatically set in Container Apps)
- Ensure authentication is configured correctly if enabled

### Voice Not Working

**No audio response from agent**

- Check browser microphone permissions (click the lock icon in address bar)
- Verify Azure AI Services deployment supports audio (Realtime models only)
- Try a different voice in `config.yaml`

**Agent doesn't hear me / cuts off early**

- Speak clearly and pause when finished
- Increase `silence_duration_ms` in `turn_detection` config
- Enable echo cancellation if using speakers (not headphones)

**Poor transcription accuracy**

- Enable noise reduction in VoiceLive config
- Use a headset instead of laptop microphone
- Check for background noise

### Evaluation Shows N/A Scores

**Intent Resolution and Coherence show N/A**

- Verify you're authenticated with Azure (`az login`)
- Check `chat_deployment` is configured in `eval/config.yaml`
- Ensure the conversation has multiple turns (single-turn conversations may not score)

**Function call metrics are 0**

- Check scenario's `expected_function_calls` matches actual plugin/function names
- Verify the agent has the required plugin assigned
- Review transcript in `eval/outputs/transcripts/` to see what happened

### Handoffs Not Working

**Agent doesn't transfer when expected**

- Verify handoff is defined in `config.yaml` (from → to)
- Check the agent's instructions mention when to transfer
- The description in the handoff helps the AI decide when to use it

### Local ACS Debugging

**Devtunnel not found**

- Verify devtunnel is installed: `devtunnel --version`
- In devcontainer: rebuild container to install devtunnel
- Manual install: `curl -sL https://aka.ms/DevTunnelCliInstall | bash`

**Error: `Not logged in to devtunnel`**

- Run `devtunnel user login --use-device-code-auth` manually
- Follow the device code flow in your browser
- Re-run `task tunnel-up`

**Error: `Port 8000 is already in use`**

- Stop any application running on port 8000 (e.g., `task run` in another terminal)
- Ensure no other dev tunnel is running (`task tunnel-down` to clean up)

**Error: `No active dev tunnel found`**

- Make sure `task tunnel-up` is running in Terminal 1
- Verify tunnel status: `devtunnel list`

**Error: `Found existing Event Grid subscription(s)`**

  You have a Terraform-managed Event Grid subscription (production). Remove it first:

  1. Edit `infra/terraform.tfvars` — set `acs_webhook_endpoint = ""`
  2. Run `task tf-plan` to review changes
  3. Run `task tf-apply` to delete the subscription
  4. Re-run `task acs-local-setup`

**Error: `App not reachable at https://...tunnel.../status`**

- Verify `task run-with-acs` is running in Terminal 2 with no errors
- Check the app started successfully (look for "Uvicorn running" message)
- Verify tunnel is forwarding correctly: `curl https://YOUR-TUNNEL-URL/status` (should return `{"status":"running"}`)

**Event Grid subscription exists but calls aren't routed**

- Verify the app is running (`task run-with-acs` in Terminal 2)
- Check tunnel is still active (Terminal 1 should show connection logs)
- Ensure the phone number is active: `az communication phonenumber show --phone-number "+44..."`
- Check Event Grid delivery status in Azure Portal → Event Grid Subscriptions → local-dev-incoming-call → Metrics

**Calls connect but hang or disconnect immediately**

- Ensure `ACS_AUTH_ENABLED=true` (automatically set by `task run-with-acs`)
- Verify the tunnel is allowing anonymous access (set by `--allow-anonymous` in `task tunnel-up`)
- Check application logs in Terminal 2 for WebSocket connection errors

**ERROR: Could not determine tunnel URL**

- Ensure the tunnel is hosting port 8000 (check output from `task tunnel-up`)
- Run `devtunnel list --json` to inspect the tunnel structure
- Verify the tunnel has started successfully (look for "Hosting tunnel" message)

**Authentication errors when calling ACS number**

- Verify `ACS_AUTH_ENABLED=true` is set by `task run-with-acs`
- Check `ACS_AUTH_ACS_RESOURCE_ID` is populated (shown in startup output)
- Ensure Azure CLI is authenticated: `az account show`

## 🔒 Security Considerations

1. **Authentication**: Uses `DefaultAzureCredential` - supports CLI locally, managed identity in production
2. **No secrets in config**: Use `${VAR_NAME}` syntax for sensitive values
3. **ACS JWT validation**: Enable `authentication.enabled` in production to validate WebSocket connections
4. **Non-root Docker**: Container runs as unprivileged user

See [ADR: Secure WebSocket Connection](docs/adrs/2026-01-27-Secure-WebSocket-Connection.md) for authentication details.

