---
name: setup-acs-local
description: Set up local ACS debugging with dev tunnels. Use when asked to test phone calls locally, debug ACS calls on localhost, set up dev tunnels, or run the app locally with real phone calls.
---

# Set Up Local ACS Debugging

You are a setup assistant helping the user test real phone calls via Azure Communication Services while running the
application locally using Azure Dev Tunnels.

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

- **Option 1** → Switch to the `setup-local` skill.
- **Option 2** → If setup is complete (`.venv/` exists, infrastructure deployed), guide the user to run `task run` and
  open `http://localhost:8000`. If setup is incomplete, tell them and offer to complete setup first via `setup-local`.
- **Option 3** → Continue with this skill (setup-acs-local) from the first incomplete step.

If the user confirms option 3, proceed to "Before You Start" below.

## Before You Start

Read `README.md` (the "Local ACS Debugging" section) to stay current with any recent changes.

Check the current state of the user's environment:

1. Check if `infra/terraform.tfstate` exists and is non-empty — infrastructure must be deployed.
2. Check if a phone number has been purchased:
   ```bash
   ACS_NAME=$(cd infra && terraform output -raw acs_name 2>/dev/null)
   ```
   If this returns empty, infrastructure isn't deployed. If it returns a value, check for purchased phone numbers:
   ```bash
   az communication phonenumber list \
     --connection-string "$(cd infra && terraform output -raw acs_connection_string)" \
     --query "[].phoneNumber" -o tsv
   ```
   If no phone numbers are returned, the user needs to purchase one with `task acs-phone-purchase`.
3. Check if `infra/terraform.tfvars` contains `acs_webhook_endpoint` with a non-empty value — if it does, there's a
   Terraform-managed Event Grid subscription that will conflict with local debugging.
4. Check if `devtunnel` is available:
   ```bash
   devtunnel --version
   ```
5. Check if a dev tunnel is already running:
   ```bash
   devtunnel list --json 2>/dev/null | jq -e '.tunnels | length > 0' >/dev/null 2>&1
   ```
6. Check if the app is already running on port 8000:
   ```bash
   lsof -i :8000 2>/dev/null
   ```

Summarise what you found to the user. If infrastructure is not deployed, tell the user: "Your Azure infrastructure
needs to be deployed and a phone number purchased before you can debug ACS calls locally. I'd recommend using the
`setup-local` skill first, then `setup-acs` to purchase a phone number."
Do not proceed until infrastructure is confirmed deployed.

Then proceed from the first incomplete step.

## Steps

This workflow requires **3 terminals** running simultaneously. Guide the user through each one.

### Step 1 — Prerequisites Check

Confirm the following are ready:

| Prerequisite | How to check |
|---|---|
| Azure infrastructure deployed | `cd infra && terraform output -raw openai_endpoint` returns a URL |
| ACS phone number purchased | `task acs-phone-purchase` was run previously |
| devtunnel CLI installed | `devtunnel --version` succeeds |
| jq installed | `jq --version` succeeds (pre-installed in the dev container) |
| No conflicting Event Grid subscription | `acs_webhook_endpoint` in `infra/terraform.tfvars` is empty or unset |

If `acs_webhook_endpoint` has a value in `infra/terraform.tfvars`, warn the user:

"There's an existing Terraform-managed Event Grid subscription that will conflict with local debugging. We need to
remove it first."

Guide them through the removal:

1. Edit `infra/terraform.tfvars` — set `acs_webhook_endpoint = ""`
2. Run `task tf-plan` to review changes
3. Run `task tf-apply` to delete the subscription

If `devtunnel` is not installed:

- **In devcontainer**: Rebuild the container — devtunnel is included automatically.
- **Manual install**: `curl -sL https://aka.ms/DevTunnelCliInstall | bash`

Only proceed once all prerequisites are confirmed.

### Step 2 — Start the Dev Tunnel (Terminal 1)

Explain: "The dev tunnel creates a public HTTPS endpoint that forwards traffic to your local port 8000. This is how ACS
will reach your local application."

Tell the user to open a **dedicated terminal** for this — the tunnel blocks and must stay running.

Run:

```bash
task tunnel-up
```

The first time, this will prompt for device code authentication. Guide the user through the login flow if needed.

Once the tunnel is running, confirm the output shows a tunnel URL (e.g., `https://XXXXX-8000.devtunnels.ms`).

**Important:** This terminal must stay open for the entire debugging session. If it closes, the tunnel stops and
calls won't route to localhost.

**Troubleshooting:**

- **`devtunnel: command not found`** — devtunnel isn't installed. See prerequisites above.
- **`Not logged in to devtunnel`** — Run `devtunnel user login --use-device-code-auth` manually, then retry.
- **`Port 8000 is already in use`** — Stop whatever is using port 8000 (`lsof -i :8000`), or stop a previous tunnel
  with `task tunnel-down`.

### Step 3 — Start the Application (Terminal 2)

Tell the user to open a **second terminal**.

Explain: "This starts the app with ACS authentication enabled and the tunnel URL as the callback host. The app will
automatically discover the tunnel URL from the active dev tunnel."

Run:

```bash
task run-with-acs
```

Confirm the startup output shows:

- `CONTAINER_APP_HOSTNAME` set to the tunnel URL
- `ACS_AUTH_ENABLED=true`
- `ACS_AUTH_ACS_RESOURCE_ID` populated with a value
- `Uvicorn running on http://127.0.0.1:8000`

**Important:** The voice debugger UI at `http://localhost:8000` will **NOT** work when authentication is enabled.
Testing must be done by calling the ACS phone number directly.

**Troubleshooting:**

- **`No active dev tunnel found`** — Make sure `task tunnel-up` is running in Terminal 1. Verify with
  `devtunnel list`.
- **`Could not determine tunnel URL`** — The tunnel may not be hosting port 8000. Check Terminal 1 output.
- **`Failed to fetch ACS immutable resource ID`** — Azure CLI credentials may have expired. Run `az login` and retry.
- **`AZURE_OPENAI_ENDPOINT` or `ACS_CONNECTION_STRING` errors** — Infrastructure may not be deployed. Run
  `cd infra && terraform output` to verify.

### Step 4 — Create Event Grid Subscription (Terminal 3)

Tell the user to open a **third terminal**.

Explain: "This creates a temporary Event Grid subscription that routes incoming ACS calls to your dev tunnel. It runs
several safety checks first."

Run:

```bash
task acs-local-setup
```

This task will:

1. Verify an active dev tunnel exists
2. Check for conflicting Terraform-managed Event Grid subscriptions
3. Perform a health check via the tunnel to ensure the app is reachable
4. Create an Event Grid subscription named `local-dev-incoming-call`

Confirm the output says "Done! Incoming calls will now route to your local app."

**Troubleshooting:**

- **`No active dev tunnel found`** — `task tunnel-up` must be running in Terminal 1.
- **`Found existing Event Grid subscription(s)`** — There's a Terraform-managed subscription. Remove it first (see
  Step 1 prerequisites).
- **`App not reachable at https://...tunnel.../status`** — The app must be running via `task run-with-acs` in
  Terminal 2. Verify the app started successfully and the tunnel is forwarding correctly.

### Step 5 — Test the Phone Call

Guide the user to test the integration:

1. **Call the ACS phone number** from a real phone (mobile or landline).
2. **Listen for the greeting** — the receptionist agent should answer and introduce itself.
3. **Try a handoff** — ask for something that should route to another agent (e.g., "I have a billing question") to
   verify handoffs work.
4. **Check Terminal 2** — you should see WebSocket connection logs and agent activity.

**Success criteria:**

- [ ] Call connects successfully
- [ ] Receptionist agent speaks a greeting
- [ ] Handoffs between agents work
- [ ] Audio quality is clear in both directions
- [ ] Terminal 2 shows request logs

If any step fails, troubleshoot:

- **Call doesn't connect** — Check Terminal 1 (tunnel active?), Terminal 2 (app running?), and verify Event Grid
  subscription exists: `az eventgrid event-subscription show --name local-dev-incoming-call --source-resource-id $(cd infra && terraform output -raw acs_id)`
- **Call connects but hangs or disconnects** — Ensure `ACS_AUTH_ENABLED=true` is set (check Terminal 2 output).
  Verify the tunnel allows anonymous access (set by `--allow-anonymous` in `task tunnel-up`).
- **No audio / agent doesn't respond** — Check Terminal 2 for WebSocket errors. Verify Azure OpenAI endpoint is
  reachable.
- **Authentication errors** — Verify `ACS_AUTH_ACS_RESOURCE_ID` is populated in Terminal 2 startup output. Re-run
  `az login` if needed.

## Teardown

When the user is done debugging, guide them through teardown **in this order**:

### 1. Delete Event Grid Subscription (Terminal 3)

```bash
task acs-local-teardown
```

This removes the `local-dev-incoming-call` Event Grid subscription. Safe to run multiple times (idempotent).

### 2. Stop the Application (Terminal 2)

Press `Ctrl+C` to stop the FastAPI app.

### 3. Stop the Dev Tunnel (Terminal 1)

Press `Ctrl+C` to stop the tunnel, or from any terminal:

```bash
task tunnel-down
```

This deletes all dev tunnels and cleans up.

## Completion

Once the test call succeeds, tell the user:

"Local ACS debugging is set up! Incoming calls to your ACS phone number will route to your local machine through the
dev tunnel. You can now debug call flows, test agent behavior, and iterate on your configuration locally."

"Remember to run `task acs-local-teardown` and stop the tunnel when you're done to clean up the temporary Event Grid
subscription."

## Important Rules

- Work through steps sequentially. Do not skip ahead.
- Confirm each step succeeds before moving to the next.
- If a step fails, troubleshoot before continuing.
- Never modify application source code — this skill only handles local ACS debugging setup.
- Always verify Azure authentication is working before attempting any Azure operations.
- The three terminals must remain open simultaneously during the debugging session.
- The voice debugger UI does not work when ACS authentication is enabled — test via real phone calls only.
- Always tear down the Event Grid subscription when done — leaving it active will route production calls to a dead
  tunnel.
- If a Terraform-managed Event Grid subscription exists, it must be removed before creating the local one.
