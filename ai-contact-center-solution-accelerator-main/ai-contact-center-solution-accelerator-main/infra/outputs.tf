# Random Suffix
output "resource_suffix" {
  description = "Random suffix appended to resource names for uniqueness"
  value       = local.suffix
}

# Resource Group
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_id" {
  description = "ID of the resource group"
  value       = azurerm_resource_group.main.id
}

# Container Registry
output "acr_login_server" {
  description = "Login server URL for the Azure Container Registry"
  value       = module.container_registry.login_server
}

output "acr_name" {
  description = "Name of the Azure Container Registry"
  value       = module.container_registry.name
}

# Container App Environment
output "container_app_environment_id" {
  description = "ID of the Container Apps Environment"
  value       = azurerm_container_app_environment.main.id
}

output "container_app_environment_name" {
  description = "Name of the Container Apps Environment"
  value       = azurerm_container_app_environment.main.name
}

# Azure AI Services
output "openai_endpoint" {
  description = "Endpoint URL for Azure AI Services"
  value       = module.azure_ai_services.endpoint
}

output "openai_deployment_name" {
  description = "Name of the realtime model deployment"
  value       = module.azure_ai_services.deployment_name
}

output "openai_transcribe_deployment_name" {
  description = "Name of the transcribe model deployment"
  value       = module.azure_ai_services.transcribe_deployment_name
}

output "openai_chat_deployment_name" {
  description = "Name of the chat model deployment (for eval module)"
  value       = module.azure_ai_services.chat_deployment_name
}

output "openai_tts_deployment_name" {
  description = "Name of the TTS model deployment (for eval module)"
  value       = module.azure_ai_services.tts_deployment_name
}

output "openai_resource_id" {
  description = "Resource ID of the Azure AI Services account"
  value       = module.azure_ai_services.id
}

# Managed Identity
output "managed_identity_id" {
  description = "ID of the managed identity for the Container App"
  value       = azurerm_user_assigned_identity.container_app.id
}

output "managed_identity_client_id" {
  description = "Client ID of the managed identity for the Container App"
  value       = azurerm_user_assigned_identity.container_app.client_id
}

output "managed_identity_principal_id" {
  description = "Principal ID of the managed identity for the Container App"
  value       = azurerm_user_assigned_identity.container_app.principal_id
}

# Azure Communication Services
output "acs_id" {
  description = "ID of the Azure Communication Services resource"
  value       = module.communication_services.id
}

output "acs_name" {
  description = "Name of the Azure Communication Services resource"
  value       = module.communication_services.name
}

output "acs_connection_string" {
  description = "Primary connection string for Azure Communication Services"
  value       = module.communication_services.primary_connection_string
  sensitive   = true
}

# Application Insights
output "application_insights_id" {
  description = "ID of the Application Insights resource"
  value       = azurerm_application_insights.main.id
}

output "application_insights_instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "application_insights_connection_string" {
  description = "Connection string for Application Insights"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

# Event Grid
output "eventgrid_system_topic_id" {
  description = "ID of the Event Grid System Topic for ACS"
  value       = module.event_grid.system_topic_id
}

output "eventgrid_system_topic_name" {
  description = "Name of the Event Grid System Topic for ACS"
  value       = module.event_grid.system_topic_name
}
