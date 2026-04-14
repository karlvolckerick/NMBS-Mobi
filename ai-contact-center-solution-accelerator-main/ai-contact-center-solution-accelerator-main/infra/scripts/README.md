# Infrastructure Scripts

Scripts for one-time infrastructure setup tasks that can't be automated via Terraform.

## Purchase Phone Number

Purchase a phone number for Azure Communication Services.

### Prerequisites

- Azure CLI installed and logged in (`az login`)
- Terraform infrastructure deployed (`task tf-apply`)
- [Task](https://taskfile.dev/) installed

### Usage

```bash
# UK toll-free (default)
task acs-phone-purchase

# US toll-free
task acs-phone-purchase -- --country US

# US geographic (local) number
task acs-phone-purchase -- --country US --type geographic

# Skip confirmation (for automation)
task acs-phone-purchase -- --auto-approve
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--country` | Country code (e.g., GB, US, DE) | GB |
| `--type` | `toll-free` or `geographic` | toll-free |
| `--auto-approve` | Skip confirmation prompt | - |

### What Happens

1. The script gets your ACS resource name from Terraform output
2. Searches for an available phone number matching your criteria
3. Shows the number and cost, asks for confirmation
4. Purchases the number and associates it with your ACS resource

Incoming calls to this number will route via Event Grid to your application.

### Verifying

After purchase, confirm in the Azure Portal:
**Communication Services** > *your resource* > **Phone numbers**
