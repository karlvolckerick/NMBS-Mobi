---
name: setup-acs
description: Set up Azure Communication Services phone integration. Use when asked to add a phone number, configure incoming calls, set up Event Grid, or enable ACS.
---

# Set Up ACS Phone Integration

You are a setup assistant helping the user connect real phone calls to the AI Contact Centre Solution Accelerator via
Azure Communication Services.

Start by briefly explaining: "I'll help you set up real phone calls via Azure Communication Services. We'll purchase a
phone number, configure Event Grid to route incoming calls, verify authentication, and test the end-to-end flow."

## Before You Start

Check the current state of the user's environment:

1. Check if `infra/terraform.tfstate` exists and is non-empty — infrastructure must be deployed.
2. Verify the Container App is running:
   ```bash
   cd infra && az containerapp show \
     --name ai-contact-centre-app \
     --resource-group $(terraform output -raw resource_group_name) \
     --query name -o tsv
   ```
3. Check if `infra/terraform.tfvars` contains `acs_webhook_endpoint` — if it does, Event Grid may already be configured.

If the Container App is not running or infrastructure is not deployed, tell the user: "Your app needs to be deployed to
Azure before setting up phone integration. I'd recommend using the `setup-deploy` skill first to build and deploy the
Container App."
Do not proceed until the Container App is confirmed running.

Summarise what you found to the user, e.g.:

- "Your Container App is running and infrastructure is deployed. You're ready to set up phone integration."
- "I can see Event Grid is already configured in your tfvars — we may be able to skip that step."
- "The Container App doesn't appear to be running. Let's get that deployed first."

Then proceed from the first incomplete step.

## Steps

Work through these steps one at a time. Confirm each step succeeds before moving on.

### Step 1 — Purchase a Phone Number

Explain: "First, we need to purchase a phone number from Azure Communication Services. This is the number callers will
dial to reach your AI contact centre."

Ask: "Which type of phone number would you like?"

1. **UK toll-free** (default) — `task acs-phone-purchase`
2. **US toll-free** — `task acs-phone-purchase -- --country US`
3. **US local number** — `task acs-phone-purchase -- --country US --type geographic`
4. **Other** — tell me the country code (e.g., DE, FR, AU) and whether you want toll-free or geographic

Wait for the user to choose before running the command.

Run the selected command. The script will:

1. Look up your ACS resource name from Terraform output
2. Search for an available phone number matching the criteria
3. Show the number and cost, and ask for confirmation
4. Purchase the number and associate it with your ACS resource

After purchase, verify by checking the Azure Portal: **Communication Services > Phone numbers**. The purchased number
should appear in the list.

**Troubleshooting:**

- **No numbers available** — Try a different country or number type. Some regions have limited availability.
- **Insufficient permissions** — Ensure your Azure account has Contributor access to the ACS resource.
- **ACS resource not found** — Infrastructure may not be fully deployed. Run `cd infra && terraform output` to check
  that `acs_connection_string` has a value.

### Step 2 — Configure Event Grid

Explain: "Event Grid routes incoming calls from your phone number to your application's webhook endpoint
(`/calls/incoming`). We need to configure the webhook URL and create the Event Grid subscription via Terraform."

Run:

```bash
task acs-event-grid-setup
```

This command:

1. Auto-detects the Container App URL from Azure
2. Constructs the webhook URL (`https://<app-url>/calls/incoming`)
3. Updates `infra/terraform.tfvars` with the `acs_webhook_endpoint` value

Next, preview the Terraform changes:

```bash
task tf-plan
```

Review the plan output with the user. It should show an Event Grid subscription being created that points to the
webhook URL. Confirm the plan looks correct before applying.

Apply the changes:

```bash
task tf-apply
```

This applies the saved plan from `tf-plan` and executes immediately — there is no confirmation prompt since the plan
was already reviewed.

**Troubleshooting:**

- **"Container App not found"** — The `acs-event-grid-setup` task requires the Container App to be deployed. Run
  `task app-up` first, then retry.
- **tf-plan shows unexpected changes** — Review carefully. If infrastructure was modified outside of Terraform, you may
  need to reconcile state.
- **Event Grid subscription fails** — Check that the webhook URL is reachable. The Container App must have external
  ingress enabled.

### Step 3 — Verify Authentication

Explain: "The `task app-up` command automatically enables JWT authentication and sets the ACS resource ID on the
Container App. Let's confirm this is configured correctly."

Verify that the Container App has authentication enabled:

```bash
cd infra && az containerapp show \
  --name ai-contact-centre-app \
  --resource-group $(terraform output -raw resource_group_name) \
  --query "properties.template.containers[0].env[?name=='ACS_AUTH_ENABLED'].value" \
  -o tsv
```

This should return `true`.

If it doesn't, re-run `task app-up` to update the Container App with the correct environment variables.

**Important note:** When ACS authentication is enabled, the voice debugger UI at the app URL will NOT work — it cannot
provide the required ACS authentication tokens. Testing must be done by calling the phone number directly.

### Step 4 — Test the Phone Number

Guide the user to test the integration:

1. **Call the purchased phone number** from a real phone (mobile or landline).
2. **Listen for the greeting** — the receptionist agent should answer and introduce itself.
3. **Try a handoff** — ask for something that should route to another agent (e.g., "I have a billing question") to
   verify handoffs work over the phone.

**Success criteria:**

- [ ] Call connects successfully
- [ ] Receptionist agent speaks a greeting
- [ ] Handoffs between agents work
- [ ] Audio quality is clear in both directions

If any step fails, troubleshoot:

- **Call doesn't connect** — Verify the Event Grid subscription is active in the Azure Portal under
  **Communication Services > Events**. Check that the webhook URL matches the Container App URL.
- **No audio / agent doesn't respond** — Check Container App logs:
  `az containerapp logs show --name ai-contact-centre-app --resource-group <rg_name> --follow`.
- **Call connects but agent sounds wrong** — Review `config.yaml` agent instructions and voice settings.

## Completion

Once all steps pass, tell the user:

"Phone integration is complete! Your AI contact centre is now accepting real phone calls. Incoming calls to
[the purchased number] will be handled by your configured agents."

"You can manage your phone numbers in the Azure Portal under **Communication Services > Phone numbers**."

## Important Rules

- Work through steps sequentially. Do not skip ahead.
- Confirm each step succeeds before moving to the next.
- If a step fails, troubleshoot before continuing.
- Never modify application source code — this skill only handles ACS phone integration setup.
- Always verify Azure authentication is working before attempting any Azure operations.
- `task tf-apply` applies a saved plan — it does NOT prompt for confirmation. Make sure the plan was reviewed first.
- `task acs-event-grid-setup` requires the Container App to exist. If it doesn't, deploy first with `task app-up`.
- The voice debugger UI does not work when ACS authentication is enabled — test via real phone calls only.
