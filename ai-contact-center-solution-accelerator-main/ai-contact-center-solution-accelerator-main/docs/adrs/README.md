# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records documenting significant technical decisions made during the
design and evolution of the AI Contact Centre Solution Accelerator.

## What Are ADRs?

ADRs are a structured way to document significant decisions made during the design of a software system. These
records capture the context, rationale, and consequences of each decision.

**Why document decisions?**
- **Transparency**: Architectural decisions are visible and accessible
- **Traceability**: Understand why specific choices were made
- **Consistency**: Encourages consistent decision-making
- **Onboarding**: Helps new engineers understand the system's evolution

## Reading ADRs

Each ADR follows this structure:

1. **Status**: accepted, proposed, deprecated, or superseded
2. **Context**: The problem being addressed
3. **Decision Drivers**: What factors influenced the choice
4. **Considered Options**: Alternatives that were evaluated
5. **Decision Outcome**: Which option was chosen and why
6. **Pros and Cons**: Trade-offs of the chosen option

Start with the ADRs most relevant to your work. For example:
- Working on voice processing? Read the VoiceLive ADR
- Adding a new agent framework? Read the Semantic Kernel ADR
- Implementing authentication? Read the Secure WebSocket ADR

## Adding an ADR

When making a significant architectural decision:

1. Copy `template.md` to a new file: `yyyy-mm-dd-<title>.md`
2. Fill in all sections with your analysis
3. Raise a PR and discuss with the team
4. Once approved and merged, the ADR is considered accepted

**What qualifies as "significant"?**
- Technology choices (frameworks, libraries)
- Architectural patterns
- External service integrations
- Security approaches
- Decisions with long-term implications

## Modifying ADRs

Once merged, ADRs should be **immutable** except for status updates.

If a decision needs to change:
1. Create a new ADR explaining the new decision
2. Update the old ADR's status to `superseded - [link to new ADR]`

This preserves the historical record of why decisions evolved.
