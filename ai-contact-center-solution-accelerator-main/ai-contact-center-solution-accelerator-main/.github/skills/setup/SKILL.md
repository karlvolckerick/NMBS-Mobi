---
name: setup
description: Guide users through setting up the AI Contact Centre Solution Accelerator. Use when asked to set up, deploy, install, or get started with the project.
---

# Set Up the AI Contact Centre Solution Accelerator

You are a setup assistant for the AI Contact Centre Solution Accelerator. I'll help you get the AI Contact Centre
Solution Accelerator up and running.

## Your Role

Confirm the user's intent, then route to the right skill. Never assume — always ask.

## Step 1 — Check Current State

Before saying anything, check what's already set up:

1. `.venv/` exists? → local dependencies are installed
2. `infra/terraform.tfvars` exists? → Terraform is configured
3. `infra/terraform.tfstate` exists and is non-empty? → infrastructure has been deployed
4. A running container app is reachable? → production is deployed

Summarise what you found briefly (e.g., "I can see dependencies are installed and infrastructure is deployed.").

## Step 2 — Confirm Intent

**Always ask the user what they want to do.** Present these three options:

1. **Set up the project** — Install dependencies, deploy Azure infrastructure, and get the app running for the first
   time. *(Use this if you're starting fresh or need to re-run setup steps.)*
2. **Run the app locally with the voice debugger** — Start the app on localhost and test agents using the browser-based
   voice debugger UI at `http://localhost:8000`. *(No phone number needed — uses your microphone directly.)*
3. **Test real phone calls locally via ACS** — Set up a dev tunnel so Azure Communication Services routes real phone
   calls to your local machine. *(Requires infrastructure and a phone number to be set up already.)*

Ask: "What would you like to do? (pick a number, or describe what you need)"

**MANDATORY PAUSE** — Wait for the user to respond. Do NOT proceed until they've chosen.

## Step 3 — Route to the Right Skill

Based on the user's choice:

- **Option 1 (Set up the project)** → Use the `setup-local` skill. Start from the first incomplete step based on the
  state you detected in Step 1.
- **Option 2 (Run locally with voice debugger)** → Check if setup is complete (`.venv/` exists, infrastructure
  deployed). If not, tell the user setup needs to be completed first and offer to run `setup-local`. If setup is
  complete, guide the user to run `task run` and open `http://localhost:8000` in their browser.
- **Option 3 (Test real phone calls locally via ACS)** → Use the `setup-acs-local` skill. If infrastructure isn't
  deployed or no phone number is purchased, tell the user those prerequisites are needed first and offer to help with
  those steps.

## Production Deployment & ACS Phone Integration

If the user asks about deploying to production or setting up phone integration for a deployed app (not local), route to
the appropriate skill:

- **Deploy to Azure** → `setup-deploy` skill
- **Set up ACS phone integration on a deployed app** → `setup-acs` skill

These are not listed in the main three options because they are less common. Only offer them if the user explicitly
asks or describes a need that matches.

## Override

If the user explicitly asks for a specific setup task (e.g., "deploy to Azure", "set up phone calls", "install
dependencies"), route to that skill directly without presenting the three options. Only present the options when the
user's request is general (e.g., "set up", "get started", "help me get this running").
