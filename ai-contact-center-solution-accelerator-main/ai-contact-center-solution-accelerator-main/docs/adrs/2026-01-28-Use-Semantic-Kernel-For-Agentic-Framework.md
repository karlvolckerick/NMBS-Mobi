# Use Semantic Kernel as the Agentic Framework

* **Status:** accepted
* **Proposer:** @adamdougal & @AlexTeslenko
* **Date:** 2026-01-28

## Context and Problem Statement

The AI Contact Centre Solution Accelerator requires an agentic framework to orchestrate real-time voice conversations 
with AI agents. The framework must support real-time voice streaming, tool calling, multi-agent handoffs, and 
integration with Azure services. Several frameworks have emerged in this space, and this ADR evaluates which is best 
suited for the accelerator's requirements.

## Decision Drivers

* Effort required to implement
* Maintainability
* GA status
* Community support
* Feature set:
  * Supports Azure Communication Services (WebSockets)
  * Supports Azure Voice Live or GPT Realtime
  * Supports tool calling
  * Supports tool switching/multi-agent
  * Supports persona switching/multi-agent
  * Supports MCP (Model Context Protocol)

## Considered Options

* [Semantic Kernel](https://github.com/microsoft/semantic-kernel)
* [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
* [LiveKit](https://livekit.io/)
* [LangChain](https://www.langchain.com/)
* [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
* [Azure Voice Live SDK](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-voicelive)

## Decision Outcome

Chosen option: "Semantic Kernel", because it meets all feature requirements including Azure Voice Live, Azure 
Communication Services, tool calling, and multi-agent support. While realtime features are in preview, the framework 
is GA and has strong community support with active Microsoft development.

**Note:** Microsoft Agent Framework is the strategic direction for agentic applications. The accelerator team should 
actively monitor the Agent Framework's development, particularly for realtime voice support. When the Agent Framework 
reaches GA with realtime voice capabilities, a migration should be evaluated.

## Pros and Cons of the Options

### Feature Matrix

| Feature / Option                       | Semantic Kernel                  | Agent Framework | LiveKit | LangChain   | OpenAI Agents SDK | Azure Voice Live SDK |
|----------------------------------------|----------------------------------|-----------------|---------|-------------|-------------------|----------------------|
| Supports Azure Communication Services  | ✅                                | ❌               | ❌       | ❌           | ✅                 | ✅                    |
| Supports Azure Voice Live              | ✅                                | ❌               | ❌       | ❌           | ❌                 | ✅                    |
| Supports Realtime                      | ✅                                | ❌               | ✅       | ✅           | ✅                 | ❌                    |
| Supports Multiple Models               | ✅                                | ❌               | ✅       | ✅           | ❌                 | ❌                    |
| Supports tool calling                  | ✅                                | ✅               | ✅       | ✅           | ✅                 | ⚠️ (Manual)          |
| Supports persona switching/multi-agent | ⚠️ (Manual)                      | N/A             | ✅       | ⚠️ (Manual) | ⚠️ (Manual)       | ⚠️ (Manual)          |
| Supports dynamic tool switching        | ✅                                | N/A             | ✅       | ✅           | ✅                 | ⚠️ (Manual)          |
| Supports MCP                           | ✅                                | ✅               | ✅       | ✅           | ✅                 | ⚠️ (Manual)          |
| Effort required to implement           | Medium                           | Very High       | High    | Low         | Low               | High                 |
| Effort to maintain                     | Medium                           | Very High       | High    | High        | High              | High                 |
| GA status                              | Framework: GA, Realtime: Preview | Preview         | GA      | GA          | Preview           | GA                   |
| Community support                      | ✅                                | ✅               | ✅       | ✅✅ (Large)  | ✅ (Growing)       | ✅                    |

### Semantic Kernel

* Good, because it meets all the feature requirements
* Good, because it has strong community support and active Microsoft development
* Good, because it supports both Azure Voice Live and GPT Realtime
* Good, because it has native support for Azure Communication Services
* Good, because it supports MCP integration
* Bad, because realtime features are only in preview
* Bad, because Microsoft Agent Framework is the strategic direction for agentic applications (though no plans to 
  deprecate Semantic Kernel as yet)
* Bad, because some patches may be required to customize behavior
* Bad, because chat agent orchestration abstraction cannot be used with realtime voice

### Microsoft Agent Framework

The Agent Framework is a new offering from Microsoft for building agentic applications. It is currently in preview and 
does not have built-in support for realtime voice applications.

* Good, because it is the strategic direction from Microsoft for building agentic applications
* Bad, because it does not support realtime voice use cases
* Bad, because the effort required to add realtime voice support is high

### LiveKit

* Good, because it supports realtime voice use cases
* Good, because it is designed for multi-agent architectures with dynamic tool and persona switching
* Good, because it has GA status
* Good, because it has a strong community
* Bad, because it does not have built-in support for Azure Communication Services (only WebRTC)
* Bad, because it does not have built-in support for Azure Voice Live
* Bad, because significant custom integration would be required

### LangChain

**Architecture:**
* Uses LangGraph ReAct agent (modern replacement for deprecated AgentExecutor)
* Native MCP integration via `langchain-mcp-adapters` with automatic tool discovery
* Streaming callbacks system for real-time feedback
* State management via LangGraph state graphs

* Good, because it is GA (stable, production-ready)
* Good, because it has the largest community support
* Good, because it has native MCP integration with automatic tool discovery
* Good, because it uses modern LangGraph architecture
* Good, because LangGraph enables flexible multi-agent orchestration
* Bad, because Azure Communication Services is not natively supported
* Bad, because Azure Voice Live API is not supported (only standard GPT Realtime API)
* Bad, because no phone integration features

**Best For:**
* Single-domain voice agents
* Web/app-based voice interactions (WebSocket, no phone calls)
* Rapid prototyping and MVPs

**Not Suitable For:**
* PSTN phone call integration
* Complex call center platforms requiring phone integration

### OpenAI Agents SDK

**Architecture:**
* Uses official `agents` library with built-in `RealtimeAgent`
* Native support for OpenAI Realtime API
* MCP integration via `mcp_servers` parameter
* Event-driven architecture with comprehensive event types

* Good, because it uses the official OpenAI library with proven patterns
* Good, because it is actively maintained by OpenAI
* Good, because voice agents are a primary use case with first-class support
* Good, because it has built-in Azure Communication Services support
* Good, because it provides rich event streaming for debugging
* Good, because MCP integration is straightforward
* Bad, because it is relatively new (less battle-tested)
* Bad, because it is not GA yet (in preview)
* Bad, because Azure Voice Live integration has authentication issues
* Bad, because it only supports OpenAI Realtime API, not Azure-specific features

**Best For:**
* Projects wanting direct OpenAI integration
* Teams prioritizing simplicity
* PSTN phone integration via ACS (with OpenAI Realtime API)

**Not Suitable For:**
* Projects requiring Azure Voice Live features (semantic VAD, Azure Speech, etc.)
* Multi-LLM provider switching

### Azure Voice Live SDK

Azure Voice Live has its own dedicated SDK for direct interaction without an agent framework abstraction.

* Good, because it has GA status
* Good, because it natively supports Azure Voice Live
* Good, because it natively supports Azure Communication Services
* Good, because it provides more control and flexibility
* Bad, because it requires significant effort to implement all required features
* Bad, because it would tie the accelerator completely to Azure Voice Live
* Bad, because it has a smaller community compared to established frameworks

## Links

* [Semantic Kernel](https://github.com/microsoft/semantic-kernel)
* [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
* [LiveKit](https://livekit.io/)
* [LangChain](https://www.langchain.com/)
* [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
* [Azure Voice Live SDK](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-voicelive)
* [Azure Communication Services](https://learn.microsoft.com/en-us/azure/communication-services/)
* [Azure Voice Live](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live)
