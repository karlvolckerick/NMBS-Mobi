---
name: setup-local
description: Set up local development environment. Use when asked to get the project running locally, install dependencies, deploy infrastructure, or start the app.
---

# Set Up Local Development Environment

You are a setup assistant helping the user get the AI Contact Centre Solution Accelerator running on their local
machine.

## Confirm Intent

This is the **first thing you do** — before checking environment state or running any commands.

Present these options:

1. **Set up the project** — Install dependencies, deploy Azure infrastructure, and get the app running for the first
   time (or re-run setup steps).
2. **Run the app locally with the voice debugger** — Start the app on localhost and test agents using the browser-based
   voice debugger UI at `http://localhost:8000`. No phone number needed.
3. **Test real phone calls locally via ACS** — Set up a dev tunnel so Azure Communication Services routes real phone
   calls to your local machine. Requires infrastructure and a phone number.

Ask: "Just to confirm — which of these are you looking to do? (pick a number, or describe what you need)"

**MANDATORY PAUSE** — Wait for the user to respond. Do NOT proceed until they've chosen.

**Routing based on response:**

- **Option 1** → Continue with this skill (setup-local) from the first incomplete step.
- **Option 2** → If setup is complete (`.venv/` exists, infrastructure deployed), guide the user to run `task run` and
  open `http://localhost:8000`. If setup is incomplete, tell them and offer to complete setup first.
- **Option 3** → Switch to the `setup-acs-local` skill.

If the user confirms option 1, proceed to "Before You Start" below.

## Before You Start

Read `README.md` (especially the Quick Start section) to stay current with any recent changes.

Check the current state of the user's environment:

1. Check if `.venv/` exists — if it does, dependencies may already be installed.
2. Check if `infra/terraform.tfvars` exists — if it does, infrastructure may already be configured.
3. Check if the app starts by looking for a running process on port 8000.

Summarise what you found to the user, e.g.:

- "It looks like you already have a virtual environment set up. We can skip dependency installation unless you want to
  refresh it."
- "I don't see `infra/terraform.tfvars` yet, so we'll need to configure that."
- "Looks like a fresh clone — we'll start from the beginning."

Then proceed from the first incomplete step.

## Steps

Work through these steps one at a time. Confirm each step succeeds before moving on.

### 1. Prerequisites Check

Automatically verify each required tool by running the following commands:

| Tool      | Check command            | Minimum version | Installation                                                                       |
|-----------|--------------------------|-----------------|------------------------------------------------------------------------------------|
| Python    | `python3 --version`      | 3.12+           | [python.org](https://www.python.org/downloads/)                                    |
| uv        | `uv --version`           | any             | [docs.astral.sh/uv](https://docs.astral.sh/uv/)                                   |
| Task      | `task --version`         | any             | [taskfile.dev](https://taskfile.dev/installation/)                                 |
| Terraform | `terraform --version`    | 1.0+            | [terraform.io](https://www.terraform.io/downloads)                                 |
| Azure CLI | `az --version`           | any             | [docs.microsoft.com](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) |

Run each check command. For each tool:

- If the command succeeds, parse the version from the output and compare it against the "Minimum version" in the table
  (where specified).
  - If the version meets or exceeds the minimum (or the minimum is listed as "any"), mark the tool as installed and
    note the version.
  - If the version is below the minimum, treat this as a failed prerequisite: tell the user their version is too old,
    explain the required minimum version, and point them to the installation link so they can upgrade.
- If the command fails (not found), report it as missing and provide the installation link.

Summarise the results to the user, e.g.: "All prerequisites are installed" or "Missing or outdated: uv, Terraform —
here are the install/upgrade links."

If any tools are missing or below the minimum required version, wait for the user to install or upgrade them and re-run
the check before proceeding.

Only proceed to Step 2 once all prerequisites are verified as installed and meeting the minimum versions.

### 2. Install Dependencies

Run:

```bash
task deps
```

Confirm that `.venv/` was created and the command completed without errors.

**Troubleshooting:**

- **`uv: command not found`** — uv is not installed. Refer back to the prerequisites table.
- **Python version error** — The project requires Python 3.12+. Check with `python3 --version`. If an older version is
  installed, guide the user to install 3.12+ and ensure it's on their PATH.
- **Permission errors** — Try running from the project root directory. Avoid `sudo`.

### 3. Azure Authentication

First, check if the user is already authenticated:

```bash
az account show
```

If this succeeds, confirm the subscription name and ID look correct. If the user is happy with the active subscription,
skip ahead to Step 4.

If the command fails or returns an error (e.g., "Please run 'az login'"), run:

```bash
az login
```

This opens a browser for Azure sign-in. Once authenticated, set the correct subscription:

```bash
az account set --subscription "YOUR_SUBSCRIPTION_NAME_OR_ID"
```

If the user doesn't know their subscription, help them find it:

```bash
az account list --output table
```

Verify the correct subscription is active:

```bash
az account show
```

Confirm the displayed subscription name and ID are correct before proceeding.

**Requirements:** The subscription needs Contributor access and Azure AI Services access with OpenAI models enabled.

**Important:** If any later step fails with a permissions error (e.g., `AuthorizationFailed`, `AuthenticationError`,
`DefaultAzureCredential failed`), come back to this step and re-run `az login` — tokens may have expired.

### 4. Terraform Configuration

Check if `infra/terraform.tfvars` already exists. If not, create it from the example:

```bash
cp infra/terraform.tfvars.example infra/terraform.tfvars
```

Then walk through the key fields one at a time:

#### 4a. `project_name`

Ask: "What would you like to name this project? This is used as a prefix for all Azure resources."

The example file defaults to `ai-contact-centre`. The user can change it if they want a different prefix.

#### 4b. `subscription_id`

Help the user get their subscription ID:

```bash
az account show --query id -o tsv
```

Paste the output into `terraform.tfvars`.

#### 4c. `location`

Ask: "Which Azure region would you like to deploy to?"

Recommend **Sweden Central** or **East US 2** — these regions support the Realtime model required by the accelerator.

If the user picks a different region, warn that Realtime model support may not be available and suggest checking
Azure documentation.

#### 4d. `openai_location`

Ask: "Do you want your OpenAI models in the same region, or a different one?"

This can differ from `location`. Explain: "Sometimes you might want compute in one region but models in another — for
example, if your preferred region doesn't support a specific model. For most users, using the same region as `location`
is fine."

#### 4e. Remaining fields

Explain: "The remaining fields (model names, API versions, tags) have sensible defaults. You can leave them as-is unless
you have specific requirements."

Briefly describe what they control:

- **Model configuration** — names and versions for gpt-realtime, gpt-4o-transcribe, gpt-4.1, and TTS deployments.
- **Tags** — Azure resource tags for organisation and cost tracking.

Only change these if the user explicitly asks.

### 5. Deploy Infrastructure

Run the following commands in order:

**Initialise Terraform:**

```bash
task tf-init
```

**Preview the deployment:**

```bash
task tf-plan
```

Review the plan output with the user. Explain what will be created:

- **Azure AI Services account** — hosts the AI models
- **Model deployments** — gpt-realtime, gpt-4o-transcribe, gpt-4.1, and TTS
- **Communication Services** — for phone call handling and telephony integration
- **Container Registry** — for building and storing container images
- **Container App Environment** — for running the app in Azure (used later for deployment)

**Apply the deployment:**

```bash
task tf-apply
```

This applies the saved plan from the previous step and executes immediately without a confirmation prompt — so make sure the plan output above looks correct before running this. This typically takes 5–10 minutes.

**Troubleshooting:**

- **Insufficient permissions** — The user needs Contributor role on the subscription. Check with
  `az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) --output table`.
- **Region unavailability** — If a resource type isn't available in the chosen region, try Sweden Central or East US 2.
- **Quota exceeded** — The subscription may have hit model deployment limits. Check Azure portal under
  Quotas or try a different region.
- **State lock errors** — If a previous run was interrupted, try `cd infra && terraform force-unlock LOCK_ID`.

### 6. Run the Application

Run:

```bash
task run
```

Confirm the server starts and shows output like:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

The app should be accessible at `http://localhost:8000`.

**Troubleshooting:**

- **`AZURE_OPENAI_ENDPOINT not configured`** — Terraform outputs weren't picked up. Run
  `cd infra && terraform output` to see the values, then check that the app is reading them correctly.
- **`DefaultAzureCredential failed`** — Azure auth has expired. Run `az login` again.
- **Port 8000 already in use** — Another process is using the port. Find it with `lsof -i :8000` and stop it, or
  change the port in the run command.

### 7. Test the Voice Debugger

Guide the user to open `http://localhost:8000` in their browser.

Walk through the test sequence:

1. **Click the microphone button** to start a voice session.
2. **Say "Hello"** — the receptionist agent should respond with a greeting.
3. **Say "I have a billing question"** — this should trigger a handoff to the billing agent (if configured in
   `config.yaml`).
4. **Verify the handoff** — the billing agent should introduce itself and handle the conversation.

**Success criteria checklist:**

- [ ] App starts without errors on `http://localhost:8000`
- [ ] Voice debugger UI loads in the browser
- [ ] Agent responds to voice input
- [ ] Handoff between agents works (if configured)

If any step fails, troubleshoot based on the browser console (F12) and terminal output.

## Completion

Once all steps pass, tell the user:

"Your local development environment is ready! You can now modify `config.yaml` to customise agents, or use `task test`
to run the test suite."

## Important Rules

- Work through steps sequentially. Do not skip ahead.
- Confirm each step succeeds before moving to the next.
- If a step fails, troubleshoot before continuing.
- Never modify application source code — this skill only handles environment setup.
- If `terraform.tfvars` already exists, ask before overwriting.
- Always verify Azure authentication is working before attempting infrastructure deployment.
