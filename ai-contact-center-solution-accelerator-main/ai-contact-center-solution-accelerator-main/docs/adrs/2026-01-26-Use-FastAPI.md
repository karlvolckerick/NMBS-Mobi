# Use FastAPI as Python Web Framework

* **Status:** accepted
* **Proposer:** @svandenhoven
* **Date:** 2026-01-26

## Context and Problem Statement

Having chosen [Python as the implementation language](2026-01-26-Use-Python.md) for the AI Contact Centre Solution 
Accelerator, a web framework is needed to build the required API endpoints and WebSocket connections. The framework must 
support real-time voice streaming, integration with Semantic Kernel, and provide a good developer experience.

## Decision Drivers

* Native async support - Critical for real-time voice streams and WebSocket connections
* Ease of integration with Semantic Kernel and Azure SDKs
* WebSocket endpoint support for bidirectional audio streaming
* Community support and long-term stability
* High scalability for concurrent voice connections
* Developer productivity and learning curve

## Considered Options

* FastAPI
* Flask
* Django
* Tornado

## Decision Outcome

Chosen option: "FastAPI", because it delivers high-performance async APIs with native WebSocket support, which is 
critical for real-time voice streaming. FastAPI provides excellent developer experience with automatic OpenAPI 
documentation and Pydantic integration for configuration validation.

## Pros and Cons of the Options

### FastAPI

* Good, because it delivers proven high-performance async APIs via ASGI
* Good, because it has native async/await and WebSocket support
* Good, because it can handle high concurrent connections for scalability
* Good, because it has a low learning curve for building quality APIs
* Good, because Pydantic integration aligns with the accelerator's configuration approach
* Good, because automatic OpenAPI documentation aids development and testing
* Bad, because it has a slightly steeper learning curve than Flask
* Bad, because it is API-focused only, not a full-stack framework (not needed for this accelerator)

### Flask

* Good, because it allows for simple and intuitive API design
* Good, because it has a very low learning curve
* Bad, because it is built on WSGI which limits async capabilities
* Bad, because it does not support WebSockets and long-lived async connections natively

### Django

* Good, because it is proven for large scalable applications
* Good, because it includes comprehensive functionality for web applications
* Bad, because it provides significant overhead for an API-only use case
* Bad, because standard Django is not optimized for async, WebSockets, and high concurrency

### Tornado

* Good, because it is built on non-blocking async I/O allowing thousands of simultaneous connections
* Good, because it has excellent WebSocket support
* Bad, because it has a steep learning curve with lower-level async primitives
* Bad, because it requires more boilerplate code than FastAPI

## Links

* [FastAPI Documentation](https://fastapi.tiangolo.com/)
* [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
* [ASGI Specification](https://asgi.readthedocs.io/)
