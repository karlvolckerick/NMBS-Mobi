# Use Python as Implementation Language

* **Status:** accepted
* **Proposer:** @lherold
* **Date:** 2026-01-26

## Context and Problem Statement

The AI Contact Centre Solution Accelerator requires a programming language choice that balances AI/ML capabilities, 
real-time voice processing, and integration with Azure services. The accelerator needs to integrate with Azure OpenAI 
Realtime API for voice conversations, use Semantic Kernel for AI orchestration and multi-agent handoffs, connect with 
Azure Communication Services for telephony, and support rapid prototyping and experimentation with AI features.

## Decision Drivers

* AI/ML SDK maturity - Support for Semantic Kernel, Azure OpenAI Realtime API, and voice processing
* Real-time capabilities - WebSocket handling, async processing for voice streams
* Azure integration - SDK support for Azure Communication Services, Event Grid, Identity
* Developer productivity - Rapid iteration on prompts, agent configurations, and call flows
* Community and samples - Availability of examples for AI voice applications

## Considered Options

* Python
* Java

## Decision Outcome

Chosen option: "Python", because Semantic Kernel's Python SDK has the most complete support for Realtime API and 
multi-agent orchestration, the AI/ML ecosystem is most mature in Python, and Azure AI SDKs are generally released 
first in Python.

## Pros and Cons of the Options

### Python

* Good, because Semantic Kernel Python SDK has full Realtime API support, multi-agent handoffs, and function calling
* Good, because the AI ecosystem (Azure AI Evaluation SDK, prompt engineering tools) is mature
* Good, because Azure SDKs for Communication Services, Event Grid, and Identity are well-maintained
* Good, because rapid iteration on agent prompts, handoff logic, and voice parameters is possible
* Good, because strong typing is available via type hints and Pydantic for configuration
* Bad, because runtime performance is lower than compiled languages (mitigated by async I/O being the bottleneck)
* Bad, because package management was historically fragmented (mitigated by modern tools like `uv`)

### Java

* Good, because it offers strong runtime performance and predictable scalability
* Good, because the ecosystem is mature for enterprise backend services
* Good, because Azure SDKs for Communication Services, Event Grid, and Identity are well-supported
* Bad, because Semantic Kernel Java SDK lacks Realtime API support and has fewer multi-agent samples
* Bad, because Microsoft Agent Framework support is currently unavailable for Java
* Bad, because more boilerplate slows experimentation with prompts and agent logic
* Bad, because Azure AI Foundry and evaluation SDKs lag behind Python releases

## Links

* [Semantic Kernel AI Services](https://learn.microsoft.com/en-us/semantic-kernel/concepts/ai-services/)
* [Azure Communication SDK for Python](https://learn.microsoft.com/en-us/python/api/overview/azure/communication)
* [Azure AI Evaluation SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-evaluation-readme)
