# GitHub Copilot Integration

This project includes a comprehensive set of GitHub Copilot customisations that let you configure, deploy, evaluate, and
extend the accelerator through natural conversation. Instead of reading documentation and running commands manually, you
can ask Copilot to do it for you.

## How It Works

The accelerator defines **skills** and **workflows** in `.github/` that teach Copilot how the project works. When you
ask Copilot a question or request a task, it automatically selects the right skill based on your intent — no special
commands or syntax needed.

> **Tip:** Open VS Code with the [GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat)
> extension installed. Open the Copilot Chat panel and select **Agent mode** — this gives Copilot full access to the
> skills and coding workflow described below. Ask mode works for simple questions, but agent mode is required for
> tasks that run commands, edit files, or use the orchestrated coding workflow.

## What You Can Ask Copilot to Do

### Configure Your Contact Centre

Ask Copilot to modify `config.yaml` without editing YAML by hand. It will walk you through each option
interactively, validate your inputs, and apply the changes.

| Task | Example prompt |
|------|---------------|
| **Add an agent** | *"Add a sales agent that handles product enquiries"* |
| **Set up handoffs** | *"Let the receptionist transfer calls to billing"* |
| **Add a tool** | *"Register a new plugin for order tracking"* |
| **Connect an MCP server** | *"Connect our CRM via MCP"* |
| **General configuration** | *"I want to configure something"* (Copilot will ask what) |

Copilot reads the current `config.yaml`, shows you what's already configured, and guides you step by step — choosing a
name, writing instructions, picking a voice, and assigning tools.

### Set Up the Project

Ask Copilot to get the project running. It detects what's already done (dependencies installed? infrastructure
deployed?) and picks up from where you left off.

| Task | Example prompt |
|------|---------------|
| **Local development** | *"Help me get this running locally"* |
| **Deploy to Azure** | *"Deploy to Azure Container Apps"* |
| **Phone integration** | *"Set up real phone calls with ACS"* |
| **General setup** | *"Set up the project"* (Copilot auto-detects the next step) |

Each setup skill checks prerequisites, runs commands, and troubleshoots errors interactively.

### Tear Down Infrastructure

| Task | Example prompt |
|------|---------------|
| **Full teardown** | *"Tear down all Azure resources"* |
| **Remove app only** | *"Delete the Container App but keep infrastructure"* |

Copilot warns before destructive operations and walks through the process step by step.

### Evaluate Agent Performance

Ask Copilot to run evaluations, review results, and fix issues — all through conversation.

| Task | Example prompt |
|------|---------------|
| **Run evaluations** | *"Run evals against my agents"* |
| **Review results** | *"How did my agents perform?"* |
| **Fix issues** | *"Why is intent resolution low?"* |
| **General eval** | *"Help me evaluate"* (Copilot auto-detects the next step) |

The eval skills configure the eval module, start the app if needed, run scenarios, present results with pass/fail
status, diagnose failures from transcripts, and suggest targeted fixes.

### Write and Modify Code

For any task that requires Python code changes — building tools, adding features, fixing bugs, refactoring — Copilot
uses an orchestrated multi-phase workflow:

1. **Planning** — A planning subagent researches the codebase and produces a detailed implementation plan
2. **Review** — You review and approve the plan before any code is written
3. **Implementation** — An implementation subagent writes code following TDD
4. **Spec review** — A spec review subagent verifies the implementation meets the plan's acceptance criteria
5. **Code review** — A code review subagent checks code quality, style, and correctness
6. **Commit** — Changes are committed (auto or manual, your choice)

This repeats for each phase of the plan, with milestone pauses every 3 phases for your review.

| Task | Example prompt |
|------|---------------|
| **Build a tool** | *"Create a tool that looks up order status from our API"* |
| **Add a feature** | *"Add retry logic to the MCP loader"* |
| **Fix a bug** | *"The handoff isn't passing conversation history"* |
| **Refactor** | *"Extract the auth logic into a separate module"* |

## Skills Reference

Skills are domain-specific instructions in `.github/skills/` that teach Copilot how to perform specific tasks.

| Skill | Description | Trigger |
|-------|-------------|---------|
| `configure` | Guide through configuration options | *"configure"*, *"set up agents"* |
| `configure-agent` | Add a new agent to `config.yaml` | *"add an agent"*, *"create an agent"* |
| `configure-handoffs` | Define call transfer routes | *"set up handoffs"*, *"add a transfer"* |
| `configure-tools` | Register or assign tools | *"add a tool"*, *"assign a plugin"* |
| `configure-mcp-server` | Connect an external MCP server | *"add an MCP server"*, *"connect a CRM"* |
| `setup` | Auto-detect setup state and guide next step | *"set up"*, *"get started"* |
| `setup-local` | Install dependencies, deploy infrastructure, run locally | *"run locally"*, *"install"* |
| `setup-deploy` | Build Docker image and deploy to Azure Container Apps | *"deploy"*, *"push to Azure"* |
| `setup-acs` | Purchase phone number and configure Event Grid | *"set up phone calls"*, *"enable ACS"* |
| `teardown` | Destroy Azure infrastructure and clean up resources | *"tear down"*, *"destroy resources"* |
| `eval` | Auto-detect eval state and guide next step | *"evaluate"*, *"run evals"* |
| `eval-run` | Configure and execute evaluation scenarios | *"run evaluations"*, *"test agents"* |
| `eval-results` | Analyse results, diagnose failures, suggest fixes | *"review results"*, *"fix scores"* |

## Coding Workflow Subagents

For code changes, Copilot delegates to specialised subagents defined in `.github/agents/`:

| Subagent | Role |
|----------|------|
| **Planning** | Researches the codebase, identifies files to change, produces a phased implementation plan |
| **Implementation** | Writes code following TDD — tests first, then minimal code to pass |
| **Spec Review** | Verifies the implementation meets the plan's acceptance criteria |
| **Code Review** | Checks code quality, style, naming, and correctness (blocks on critical/major issues) |

## Project Conventions Copilot Follows

The Copilot instructions enforce these project conventions automatically:

- **YAGNI** — Only builds what was asked for, no speculative features
- **TDD** — Writes tests first, verifies they fail correctly, then implements
- **DRY** — Avoids duplication without premature abstraction
- **Bite-sized phases** — Each implementation phase addresses one concern
- **Conventional commits** — Commit messages use `fix:`, `feat:`, `chore:`, etc.
- **Existing patterns** — Reads current code before proposing new patterns

## Customising Copilot Behaviour

The Copilot configuration lives in:

```
.github/
├── copilot-instructions.md    # Main orchestration rules and routing logic
├── agents/                    # Subagent definitions for the coding workflow
│   ├── planning-subagent.agent.md
│   ├── implement-subagent.agent.md
│   ├── spec-review-subagent.agent.md
│   └── code-review-subagent.agent.md
└── skills/                    # Domain-specific skills
    ├── configure/
    ├── configure-agent/
    ├── configure-handoffs/
    ├── configure-mcp-server/
    ├── configure-tools/
    ├── setup/
    ├── setup-local/
    ├── setup-deploy/
    ├── setup-acs/
    ├── teardown/
    ├── eval/
    ├── eval-run/
    └── eval-results/
```

To add a new skill, create a new directory under `.github/skills/` with a `SKILL.md` file, then update
`.github/copilot-instructions.md` to document when and how Copilot should route requests to the new skill.

To modify how a skill works, edit its `SKILL.md` file. Changes take effect immediately in new Copilot conversations.
