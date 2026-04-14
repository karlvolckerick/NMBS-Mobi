terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  subscription_id = var.subscription_id
  resource_provider_registrations = "none"
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# Random suffix for globally unique resource names
resource "random_string" "suffix" {
  length  = 6
  lower   = true
  upper   = false
  numeric = true
  special = false
}

locals {
  suffix = random_string.suffix.result
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}-${local.suffix}"
  location = var.location
  tags     = var.tags
}

# Log Analytics Workspace (required for Container Apps)
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project_name}-logs-${local.suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

# Container Registry Module
module "container_registry" {
  source = "./modules/container-registry"

  name                = "${var.project_name}-acr-${local.suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = var.tags
}

# Azure AI Services Module
module "azure_ai_services" {
  source = "./modules/azure-ai-services"

  name                = "${var.project_name}-aiservices-${local.suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.openai_location
  tags                = var.tags

  deployment_name = var.openai_deployment_name
  model_name      = var.openai_model_name
  model_version   = var.openai_model_version
  model_capacity  = var.openai_model_capacity

  transcribe_deployment_name = var.transcribe_deployment_name
  transcribe_model_name      = var.transcribe_model_name
  transcribe_model_version   = var.transcribe_model_version
  transcribe_model_capacity  = var.transcribe_model_capacity

  chat_deployment_name = var.chat_deployment_name
  chat_model_name      = var.chat_model_name
  chat_model_version   = var.chat_model_version
  chat_model_capacity  = var.chat_model_capacity

  tts_deployment_name = var.tts_deployment_name
  tts_model_name      = var.tts_model_name
  tts_model_version   = var.tts_model_version
  tts_model_capacity  = var.tts_model_capacity
}

# Azure Communication Services Module
module "communication_services" {
  source = "./modules/communication-services"

  name                = "${var.project_name}-acs-${local.suffix}"
  resource_group_name = azurerm_resource_group.main.name
  data_location       = var.acs_data_location
  tags                = var.tags
}

# Application Insights (linked to Log Analytics workspace)
resource "azurerm_application_insights" "main" {
  name                = "${var.project_name}-appinsights-${local.suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  tags                = var.tags
}

# Diagnostic Settings: Azure AI Services -> Application Insights
resource "azurerm_monitor_diagnostic_setting" "ai_services" {
  name                           = "ai-services-diagnostics"
  target_resource_id             = module.azure_ai_services.id
  log_analytics_workspace_id     = azurerm_log_analytics_workspace.main.id
  log_analytics_destination_type = "Dedicated"

  enabled_log {
    category = "Audit"
  }

  enabled_log {
    category = "RequestResponse"
  }

  enabled_log {
    category = "Trace"
  }

  enabled_metric {
    category = "AllMetrics"
  }
}

# Container App Environment (created here, app deployed via CLI)
resource "azurerm_container_app_environment" "main" {
  name                       = "${var.project_name}-env-${local.suffix}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  tags                       = var.tags
}

# User Assigned Managed Identity for Container App
resource "azurerm_user_assigned_identity" "container_app" {
  name                = "${var.project_name}-identity-${local.suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = var.tags
}

# Role Assignment: Container App Identity -> Cognitive Services User
resource "azurerm_role_assignment" "container_app_aiservices" {
  scope                = module.azure_ai_services.id
  role_definition_name = "Cognitive Services User"
  principal_id         = azurerm_user_assigned_identity.container_app.principal_id
}

# Role Assignment: Container App Identity -> ACR Pull
resource "azurerm_role_assignment" "container_app_acr" {
  scope                = module.container_registry.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.container_app.principal_id
}

# Event Grid Module for ACS incoming call notifications
module "event_grid" {
  source = "./modules/event-grid"

  name                      = "${var.project_name}-eventgrid-${local.suffix}"
  resource_group_name       = azurerm_resource_group.main.name
  communication_services_id = module.communication_services.id
  webhook_endpoint          = var.acs_webhook_endpoint
  tags                      = var.tags
}

