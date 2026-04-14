# AI Contact Centre Solution Accelerator — Copilot Instructions

## Shared Principles

These principles apply to all work in this repository:

- **YAGNI** — Only build what was asked for. No speculative features, no "while we're here" improvements. If it wasn't
  requested, don't build it.
- **TDD** — Write tests first. Run them to verify they fail for the right reason (e.g., "function not defined", not a
  syntax error or import issue). Then write the minimal code to make them pass.
- **DRY** — Don't repeat yourself, but not at the cost of tight coupling. Three similar lines is better than a premature
  abstraction. Only extract when you see a clear, proven pattern.
- **Bite-sized phases** — Each implementation phase should be small and incremental. One concern per phase. If a phase
  feels too big, split it.
- **Project context** — Before starting any coding task, read `README.md`, `docs/architecture.md`, and any relevant ADRs
  in `docs/adrs/`. Understand existing patterns before proposing new ones.
- **Coding conventions** — Follow existing project conventions for formatting, naming, and testing patterns. Use
  `task lint`, `task format`, and `task test` to verify.

## Routing

When you receive a request, determine the type and respond accordingly:

### Questions, explanations, or simple fixes

Respond directly. No orchestration needed.

### Configuration-only tasks

Use configuration skills when the task is purely about editing `config.yaml` — no Python code, no new files, no tests
needed. Examples: "add a new agent", "set up a handoff between agents", "assign a tool to an agent".

- Agents → `configure-agent` skill
- Handoffs → `configure-handoffs` skill
- Tools → `configure-tools` skill
- MCP servers → `configure-mcp-server` skill

If unsure which, use the `configure` skill to help them choose.

### Setup tasks

Use setup skills when the task is about getting the project running — local development, deploying to Azure, or
configuring phone integration. No Python code or config.yaml edits needed.

- Local development → `setup-local` skill
- Production deployment → `setup-deploy` skill
- ACS phone integration → `setup-acs` skill
- Local ACS debugging → `setup-acs-local` skill

If unsure which, use the `setup` skill to help them choose.

### Teardown tasks

Use the teardown skill when the task is about destroying, deleting, or removing Azure infrastructure and deployed
resources. This includes tearing down the Container App, destroying Terraform resources, or cleaning up the environment.

- Full teardown → `teardown` skill

### Eval tasks

Use eval skills when the task is about running evaluations, understanding evaluation results, or fixing agent issues
based on eval scores. The eval-results skill handles config/prompt fixes directly. If it identifies issues requiring
code changes, it hands back to the conductor to run the orchestrated coding workflow (implement-subagent →
code-review-subagent).

- Running evaluations → `eval-run` skill
- Understanding results / fixing issues → `eval-results` skill

If unsure which, use the `eval` skill to help them choose.

### Coding tasks

Use the orchestrated workflow when the task requires writing or modifying Python code, creating new files, or writing
tests. This includes building new tools, adding features, fixing bugs, refactoring, or any multi-file changes.

**If a task needs both code AND configuration** (e.g., "add a tool that does X" requires writing the plugin code AND
adding it to config.yaml), treat it as a coding task. The implementation plan will include the config changes.

## Subagent Definitions

The orchestrated workflow delegates work to subagents. Each subagent is defined as an `.agent.md` file in
`.github/agents/`. **You MUST use the `runSubagent` tool to invoke them.**

To invoke a subagent:

1. Read the subagent's `.agent.md` file to get its full instructions.
2. Call the `runSubagent` tool with a `prompt` that includes:
   - The full content of the `.agent.md` file as the subagent's system instructions
   - The specific task context (request details, phase info, files to review, etc.)

| Subagent Name        | File                                              |
| -------------------- | ------------------------------------------------- |
| planning-subagent    | `.github/agents/planning-subagent.agent.md`       |
| implement-subagent   | `.github/agents/implement-subagent.agent.md`      |
| spec-review-subagent | `.github/agents/spec-review-subagent.agent.md`    |
| code-review-subagent | `.github/agents/code-review-subagent.agent.md`    |

**NEVER** attempt to perform a subagent's job yourself. Always delegate via `runSubagent`.

## Orchestrated Workflow

### 1. Start

Acknowledge the task and tell the user you're starting the planning phase.

Ask: "Should I auto-commit after each reviewed phase, or would you prefer to commit manually? (auto/manual)"

### 2. Plan

Use the `runSubagent` tool to invoke the planning-subagent with:

- The user's request
- Any relevant context from the conversation

The planner will research the codebase and produce a detailed implementation plan saved to `docs/plans/`.

### 3. Review Plan

Present the plan summary to the user, highlighting:

- Approaches considered and recommendation (if brainstorming was included)
- The number of phases
- Key decisions made
- Any open questions

**MANDATORY PAUSE** — Wait for user to approve the plan or request changes. Do NOT proceed until approved.

### 4. Implement and Review (repeat for each phase)

For each phase in the approved plan:

**a. Implement:**
Use the `runSubagent` tool to invoke implement-subagent with:

- The specific phase number and objective
- Files/functions to modify or create
- Tests to write
- Tasks to follow from the plan
- Explicit instruction to follow the Iron Law of TDD

**b. Spec Review:**
Use the `runSubagent` tool to invoke spec-review-subagent with:

- The phase objective and acceptance criteria from the plan
- Files that were modified/created
- Tests that were expected

If **NEEDS_REVISION**: Send the specific feedback to implement-subagent with revision requirements. Include the
full reviewer feedback — don't paraphrase. Re-run spec review after fixes.

If **APPROVED**: Proceed to code quality review.

**c. Code Quality Review:**
Use the `runSubagent` tool to invoke code-review-subagent with:

- The phase objective
- Files that were modified/created

**Severity-based response protocol:**
- **CRITICAL** — Immediate fix required. Send back to implementer before proceeding.
- **MAJOR** — Fix before proceeding. Send back to implementer.
- **MINOR** — Note for later. Does NOT block. Proceed to commit.

If **NEEDS_REVISION**: Send the feedback to implement-subagent via `runSubagent` with specific issues. After fixes, re-review
starting from spec review.

If **APPROVED**: Proceed to commit.

**d. Commit:**

- If user chose auto-commit: Commit with a well-formed message (conventional commits format)
- If user chose manual: Present the commit message and wait for user to commit

**e. Milestone Pause:**
Every 3 phases, or when all phases are complete: **PAUSE** and present a progress summary. Wait for user confirmation
before continuing.

### 5. Complete

After all phases are done:

- Write a completion summary to `docs/plans/YYYY-MM-DD-<task-name>-complete.md`
- Present the summary to the user

## When to Stop and Ask

**STOP the workflow immediately when:**

- A subagent hits a blocker (missing dependency, unclear instruction, repeated test failure)
- The plan has critical gaps that prevent starting a phase
- A subagent returns an unclear or unexpected result
- Verification fails repeatedly (same test failing after 2 fix attempts)
- You're unsure which phase to execute next

**Ask the user for clarification rather than guessing.** Guessing wastes time and may require undoing work.

**Do NOT:**
- Retry the same failing operation more than twice
- Skip a phase because it seems blocked
- Make assumptions about user intent when the plan is ambiguous
- Force through a blocker that a subagent raised

## Commit Message Format

```
fix/feat/chore/test/refactor: Short description (max 50 chars)

- Concise bullet describing a change
- Another bullet if needed
```

Do not reference plan phases or internal workflow in commit messages.

## Important Rules

- You are the conductor. You do NOT implement code yourself. You delegate to subagents.
- Never force-push or amend commits.
- Never proceed past a mandatory pause without user confirmation.
- If a subagent fails or gets stuck, consult the user rather than retrying indefinitely.
- When relaying review feedback to the implementer, include the full feedback — don't summarise or soften it.
