---
name: setup-deploy
description: Deploy to production on Azure. Use when asked to deploy, push to Azure, set up Docker, or run in the cloud.
---

# Deploy to Azure Container Apps

You are a deployment assistant helping the user deploy the AI Contact Centre Solution Accelerator to Azure Container
Apps.

Start by briefly explaining: "I'll help you deploy the accelerator to Azure Container Apps. We'll build a Docker image,
push it to Azure Container Registry, and deploy it as a Container App."

## Before You Start

Check the current state of the user's environment:

1. Check if `.venv/` exists — if it doesn't, the local setup hasn't been completed.
2. Check if `infra/terraform.tfvars` exists — if it doesn't, infrastructure hasn't been configured.
3. Check if `infra/terraform.tfstate` exists and is non-empty — if it doesn't, infrastructure hasn't been deployed.
4. Check Docker is installed by running `docker --version`.

If any of prerequisites 1–3 are missing, tell the user: "It looks like your local environment isn't fully set up yet.
I'd recommend running the `setup-local` skill first to install dependencies and deploy the Azure infrastructure."
Do not proceed until all prerequisites are met.

If Docker is not installed, provide the install link: [docker.com](https://docs.docker.com/get-docker/) and wait for
the user to confirm installation.

Summarise what you found to the user, e.g.:

- "Local environment is set up, infrastructure is deployed, and Docker is available. You're ready to deploy."
- "Everything looks good except Docker isn't installed — let's get that sorted first."

## Options

Ask: "How would you like to proceed?"

1. **Full deployment** — One command does everything (`task deploy`)
2. **Step-by-step deployment** — Go through each step individually
3. **Just Docker locally** — Build and run in Docker without deploying to Azure

Wait for the user to choose before proceeding.

## Option 1 — Full Deployment

Explain: "`task deploy` runs the full deployment pipeline in sequence: `tf-init` → `tf-plan` → `tf-apply` → `acr-push`
→ `app-up`. This will initialise Terraform, plan and apply any infrastructure changes, build and push the Docker image
to ACR, and deploy the Container App."

Confirm the user wants to proceed before running.

Run:

```bash
task deploy
```

Monitor the output. The steps are:

1. **tf-init** — Initialises Terraform providers and backend.
2. **tf-plan** — Creates an execution plan. Review the output with the user.
3. **tf-apply** — Applies the saved plan immediately (no confirmation prompt — the plan was already reviewed).
4. **acr-push** — Builds a `linux/amd64` Docker image and pushes it to Azure Container Registry. This may take a few
   minutes.
5. **app-up** — Deploys the Container App with all environment variables auto-configured from Terraform outputs.

Once complete, verify the deployment:

```bash
cd infra && az containerapp show \
  --name ai-contact-centre-app \
  --resource-group $(terraform output -raw resource_group_name) \
  --query "properties.configuration.ingress.fqdn" \
  -o tsv
```

Open the URL in a browser to confirm the app is running.

**Troubleshooting:**

- **ACR login failed** — Run `az login` to refresh credentials, then retry. Ensure your account has push access to the
  container registry.
- **Docker build failed** — Make sure Docker is running (`docker info`). Check the Dockerfile for syntax errors. Ensure
  you're running from the project root.
- **Image push failed** — Verify ACR login with `az acr login --name <acr_name>`. Check network connectivity.
- **Container App deployment failed** — Check the resource group and environment names match Terraform outputs. Run
  `cd infra && terraform output` to verify values.
- **tf-plan shows unexpected changes** — Review the plan carefully. If infrastructure was modified outside of Terraform,
  you may need to reconcile state.

## Option 2 — Step-by-Step Deployment

Work through these steps one at a time. Confirm each step succeeds before moving on.

### Step 1 — Infrastructure (if needed)

If the infrastructure is already deployed and no changes are needed, skip to Step 2.

**Initialise Terraform:**

```bash
task tf-init
```

**Preview changes:**

```bash
task tf-plan
```

Review the plan output with the user. If there are no changes, move on to Step 2.

**Apply changes:**

```bash
task tf-apply
```

This applies the saved plan from `tf-plan` and executes immediately without a confirmation prompt — the plan was already
reviewed in the previous step. Wait for it to complete.

**Troubleshooting:**

- **State lock errors** — If a previous run was interrupted, try `cd infra && terraform force-unlock LOCK_ID`.
- **Insufficient permissions** — The user needs Contributor role on the subscription.

### Step 2 — Build and Push Docker Image

Run:

```bash
task acr-push
```

This does three things:

1. Builds a Docker image for the `linux/amd64` platform (required for Azure Container Apps).
2. Logs into Azure Container Registry using your Azure CLI credentials.
3. Pushes the image to ACR tagged as `latest`.

This may take a few minutes, especially on the first build.

**Troubleshooting:**

- **Docker not running** — Start Docker Desktop or the Docker daemon. Verify with `docker info`.
- **ACR login failed** — Run `az login` to refresh credentials. Then retry `task acr-push`.
- **Build failed on linux/amd64** — If you're on Apple Silicon (M1/M2/M3), Docker Desktop must have Rosetta emulation
  enabled, or use `docker buildx` (which `task acr-push` handles via `--platform linux/amd64`).
- **Push timeout** — Check network connectivity. Large images may take time on slower connections.

### Step 3 — Deploy Container App

Run:

```bash
task app-up
```

This deploys (or updates) the Container App with the following auto-configured environment variables from Terraform
outputs:

| Variable                    | Description                                  |
|-----------------------------|----------------------------------------------|
| `AZURE_OPENAI_ENDPOINT`    | Azure OpenAI service endpoint                |
| `AZURE_OPENAI_DEPLOYMENT`  | OpenAI model deployment name                 |
| `ACS_CONNECTION_STRING`    | Azure Communication Services connection      |
| `AZURE_CLIENT_ID`          | Managed identity client ID for auth          |
| `ACS_AUTH_ENABLED`         | Set to `true` — enables ACS authentication   |
| `ACS_AUTH_ACS_RESOURCE_ID` | ACS resource ID for token validation          |

The app is deployed with external ingress on port 80, using a user-assigned managed identity.

### Step 4 — Verify Deployment

Get the app URL:

```bash
cd infra && az containerapp show \
  --name ai-contact-centre-app \
  --resource-group $(terraform output -raw resource_group_name) \
  --query "properties.configuration.ingress.fqdn" \
  -o tsv
```

Open the URL in a browser to confirm the app is running.

**Troubleshooting:**

- **App not reachable** — Check that ingress is configured as external:
  `az containerapp ingress show --name ai-contact-centre-app --resource-group <rg_name>`.
- **App crashes on startup** — Check logs:
  `az containerapp logs show --name ai-contact-centre-app --resource-group <rg_name> --follow`.
- **Environment variable issues** — Verify env vars are set correctly:
  `az containerapp show --name ai-contact-centre-app --resource-group <rg_name> --query "properties.template.containers[0].env"`.

## Option 3 — Local Docker Only

This builds and runs the Docker image locally without deploying to Azure. Useful for testing the containerised app
before pushing to production.

### Build the Image

Run:

```bash
task docker-build
```

This builds a Docker image tagged as `ai-contact-centre:v0.0.1`.

### Run the Container

Run:

```bash
task docker-run
```

This starts the container with:

- Port mapping: `8000` (host) → `80` (container)
- Config file mounted read-only: `config.yaml` → `/app/config.yaml`

The app will be available at `http://localhost:8000`.

**Note:** You'll need to provide the required environment variables for the app to function (e.g.,
`AZURE_OPENAI_ENDPOINT`, `ACS_CONNECTION_STRING`). You can either:

- Export them in your shell before running `task docker-run`
- Or add `-e VAR=value` flags by running docker manually:
  ```bash
  docker run -it --rm \
    -p 8000:80 \
    -v $(pwd)/config.yaml:/app/config.yaml:ro \
    -e AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/ \
    -e ACS_CONNECTION_STRING=endpoint=https://... \
    ai-contact-centre:v0.0.1
  ```

**Troubleshooting:**

- **Port 8000 already in use** — Stop whatever is using it (`lsof -i :8000`) or change the port mapping.
- **Config file not found** — Make sure you're running from the project root where `config.yaml` exists.
- **Container exits immediately** — Check logs with `docker logs <container_id>`. Missing environment variables are the
  most common cause.

## Completion

Once deployment is verified, tell the user:

"Your app is deployed and running at `https://<app-url>`. You can view logs with
`az containerapp logs show --name ai-contact-centre-app --resource-group <rg_name> --follow`."

"To accept real phone calls, use the `setup-acs` skill to configure ACS phone integration."

## Important Rules

- Work through steps sequentially. Do not skip ahead.
- Confirm each step succeeds before moving to the next.
- If a step fails, troubleshoot before continuing.
- Never modify application source code — this skill only handles deployment.
- Always verify Azure authentication is working before attempting any Azure operations.
- `task tf-apply` applies a saved plan — it does NOT prompt for confirmation. Make sure the plan was reviewed first.
- `task acr-push` builds for `linux/amd64` regardless of the host architecture.
