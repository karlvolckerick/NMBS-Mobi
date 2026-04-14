```skill
---
name: teardown
description: Tear down Azure infrastructure and clean up all deployed resources. Use when asked to tear down, destroy, delete, or remove the deployed environment.
---

# Tear Down Azure Infrastructure

You are a teardown assistant helping the user remove all Azure resources created by the AI Contact Centre Solution
Accelerator.

Start by briefly explaining: "I'll help you tear down your Azure infrastructure. This will delete the Container App,
destroy all Terraform-managed resources, and clean up the resource group."

## Before You Start

Check the current state of the user's environment:

1. Check if `infra/terraform.tfstate` exists and is non-empty — if it doesn't, there may be nothing to tear down.
2. Check if a Container App exists:
   ```bash
   cd infra && az containerapp show \
     --name ai-contact-centre-app \
     --resource-group $(terraform output -raw resource_group_name) \
     --query name -o tsv 2>/dev/null
   ```
3. Check what resources are currently in Terraform state:
   ```bash
   cd infra && terraform state list
   ```

Summarise what you found to the user, e.g.:

- "I can see a Container App and 16 Terraform-managed resources. I'll tear everything down."
- "No Container App found, but there are Terraform resources to destroy."
- "Terraform state is empty — there's nothing to tear down."

If there's nothing to tear down, tell the user and stop.

## Options

Ask: "How would you like to proceed?"

1. **Full teardown** — One command does everything (`task teardown`)
2. **Step-by-step teardown** — Go through each step individually
3. **Just delete the Container App** — Remove the app but keep infrastructure (`task app-down`)

Wait for the user to choose before proceeding.

## Option 1 — Full Teardown

Explain: "`task teardown` runs the full teardown pipeline: `app-down` → `tf-destroy`. This first deletes the Container
App (which was created outside of Terraform by `az containerapp up`), then destroys all Terraform-managed
infrastructure."

**IMPORTANT:** Warn the user: "This will permanently delete all Azure resources including the phone number, AI model
deployments, and all data. This cannot be undone."

Confirm the user wants to proceed before running.

Run:

```bash
task teardown
```

Monitor the output. The steps are:

1. **app-down** — Checks for and deletes the Container App. This must happen first because the Container App Environment
   cannot be deleted while it still contains apps.
2. **tf-destroy** — Destroys all Terraform-managed resources (AI Services, Communication Services, Container Registry,
   Container App Environment, Event Grid, role assignments, resource group).

**Troubleshooting:**

- **Container App Environment conflict (409)** — The Container App wasn't fully deleted before Terraform tried to
  remove the environment. Wait a minute and retry `task tf-destroy`.
- **State lock errors** — If a previous run was interrupted, try `cd infra && terraform force-unlock LOCK_ID`.
- **Resources already deleted manually** — If resources were deleted outside Terraform, run
  `cd infra && terraform refresh` to sync state, then retry.
- **Terraform destroy hangs on Container App Environment** — This resource can take 5+ minutes to delete. Be patient.
  If it times out, delete the resource group directly:
  `az group delete --name <resource_group_name> --yes --no-wait`
  Then clean up Terraform state:
  `cd infra && terraform state list | xargs -I {} terraform state rm {}`

## Option 2 — Step-by-Step Teardown

Work through these steps one at a time. Confirm each step succeeds before moving on.

### Step 1 — Delete the Container App

The Container App is created by `az containerapp up` (not managed by Terraform), so it must be deleted separately
before Terraform can destroy the Container App Environment.

Run:

```bash
task app-down
```

This checks for the Container App and deletes it if found. If no Container App exists, it skips gracefully.

### Step 2 — Destroy Terraform Infrastructure

Preview what will be destroyed:

```bash
cd infra && terraform plan -destroy
```

Review the plan output with the user. It should show all resources being destroyed.

Once confirmed, run:

```bash
task tf-destroy
```

This will prompt for confirmation before proceeding.

**Troubleshooting:**

- **Container App Environment 409 error** — The Container App wasn't deleted or hasn't finished deleting. Wait a minute
  and retry, or run `task app-down` again.
- **Destroy hangs** — Container App Environment deletion can take 5+ minutes. If it exceeds 10 minutes, cancel and
  delete the resource group directly:
  ```bash
  az group delete --name <resource_group_name> --yes --no-wait
  cd infra && terraform state list | xargs -I {} terraform state rm {}
  ```

### Step 3 — Verify Cleanup

Confirm the resource group no longer exists:

```bash
az group show --name <resource_group_name> 2>/dev/null && echo "Still exists" || echo "Deleted"
```

Confirm Terraform state is empty:

```bash
cd infra && terraform state list
```

If state is empty, teardown is complete.

## Option 3 — Just Delete the Container App

Run:

```bash
task app-down
```

This deletes only the Container App, leaving all other infrastructure (AI Services, Communication Services, etc.)
intact. Useful when you want to redeploy the app without rebuilding infrastructure.

After deletion, you can redeploy with `task acr-push && task app-up`.

## Completion

Once teardown is verified, tell the user:

"All Azure resources have been destroyed. The Terraform state is clean. Your `terraform.tfvars` and
`infra/terraform.tfstate` files remain so you can redeploy later with `task deploy`."

"Note: If you purchased a phone number, it has been released and cannot be recovered."

## Important Rules

- Always delete the Container App BEFORE running `terraform destroy` — this prevents 409 conflicts.
- Work through steps sequentially. Do not skip ahead.
- Confirm the user wants to proceed before destroying resources — this is a destructive operation.
- Never modify application source code — this skill only handles teardown.
- If `terraform destroy` fails on Container App Environment, the resource group delete + state cleanup is the
  reliable fallback.
- `task tf-destroy` prompts for confirmation. `task teardown` runs `app-down` then `tf-destroy` in sequence.

```
