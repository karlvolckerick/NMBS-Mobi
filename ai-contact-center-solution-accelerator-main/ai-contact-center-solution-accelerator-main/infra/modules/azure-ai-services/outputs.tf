output "id" {
  description = "ID of the Azure AI Services account"
  value       = azurerm_ai_services.main.id
}

output "endpoint" {
  description = "Endpoint URL for Azure AI Services"
  value       = azurerm_ai_services.main.endpoint
}

output "deployment_name" {
  description = "Name of the model deployment"
  value       = azurerm_cognitive_deployment.realtime.name
}

output "transcribe_deployment_name" {
  description = "Name of the transcribe model deployment"
  value       = azurerm_cognitive_deployment.transcribe.name
}

output "chat_deployment_name" {
  description = "Name of the chat model deployment"
  value       = azurerm_cognitive_deployment.chat.name
}

output "tts_deployment_name" {
  description = "Name of the TTS model deployment"
  value       = azurerm_cognitive_deployment.tts.name
}

output "principal_id" {
  description = "Principal ID of the system-assigned managed identity"
  value       = azurerm_ai_services.main.identity[0].principal_id
}
