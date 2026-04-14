# Secure WebSocket Connection with Access Tokens

* **Status:** accepted
* **Proposer:** @svandenhoven
* **Date:** 2026-01-27

## Context and Problem Statement

The AI Contact Centre Solution Accelerator communicates with clients through a WebSocket-based connection to enable 
real-time voice streaming. There are three types of clients that connect with the accelerator:

1. Azure Communication Services (ACS) - for handling phone calls
2. The Evaluation Module - for automated testing of voice conversations
3. The Voice Call Debugger - a browser-based tool for testing and debugging

These clients must have a secured and authorized connection through the WebSocket endpoint. This ADR describes the 
options for implementing authentication and authorization on the WebSocket connection.

## Decision Drivers

* All endpoints, including the WebSocket endpoint, must only accept connections from authenticated clients and enforce 
  authorization rules
* The authentication and authorization must use well-known, industry-standard patterns
* Azure Communication Services requires JWT-based authentication for WebSocket connections
* The accelerator should support a consistent authentication approach to ensure simplicity and security
* The WebSocket endpoint must be accessible via a public endpoint for ACS integration, requiring robust authentication

## Considered Options

* API Key Authentication
* Access Token (JWT) Authentication

## Decision Outcome

Chosen option: "Access Token (JWT) Authentication", because access tokens are the industry standard for authentication, 
provide better security than API keys, and are the only authentication method supported by Azure Communication Services.

For the Voice Call Debugger (browser-based), browsers do not allow custom headers on WebSocket connections. The 
debugger should only be used in non-production environments with appropriate network restrictions.

## Pros and Cons of the Options

### API Key Authentication

Using an API Key in the header that is validated by the accelerator.

* Good, because it allows simple implementation
* Bad, because JavaScript in browsers does not allow custom headers on WebSocket connections, requiring workarounds 
  with subprotocols
* Bad, because Azure Communication Services does not support API key authentication for WebSocket connections

### Access Token (JWT) Authentication

The WebSocket endpoint only allows connections with a valid JWT access token. Azure Communication Services provides its 
own access token as described in the [ACS Call Automation documentation](https://learn.microsoft.com/en-us/azure/communication-services/how-tos/call-automation/secure-webhook-endpoint?pivots=programming-language-python#call-automation-websocket-events).

The access token must be:
* Created for the correct audience
* Issued by a valid issuer
* Signed by a valid key
* Contains the required claims

* Good, because it is supported natively by Azure Communication Services
* Good, because it follows industry-standard authentication patterns
* Good, because many SDKs exist for token validation across languages
* Good, because tokens can be short-lived, reducing security risk if compromised
* Bad, because it requires app registration for non-ACS clients to request access tokens
* Bad, because it requires validation logic for ACS tokens (JWKS-based)
* Bad, because browsers cannot send custom headers on WebSocket connections, limiting browser-based clients
* Bad, because it is more complex than API keys, requiring token issuing, validation, and refresh

## Links

* [ACS Call Automation - Secure Webhook Endpoint](https://learn.microsoft.com/en-us/azure/communication-services/how-tos/call-automation/secure-webhook-endpoint?pivots=programming-language-python#call-automation-websocket-events)
* [Azure Communication Services Authentication](https://learn.microsoft.com/en-us/azure/communication-services/concepts/authentication)
