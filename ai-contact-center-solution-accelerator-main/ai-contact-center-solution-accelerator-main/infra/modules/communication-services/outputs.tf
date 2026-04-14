output "id" {
  description = "ID of the Azure Communication Services resource"
  value       = azurerm_communication_service.main.id
}

output "name" {
  description = "Name of the Azure Communication Services resource"
  value       = azurerm_communication_service.main.name
}

output "primary_connection_string" {
  description = "Primary connection string for the Communication Services resource"
  value       = azurerm_communication_service.main.primary_connection_string
  sensitive   = true
}

output "secondary_connection_string" {
  description = "Secondary connection string for the Communication Services resource"
  value       = azurerm_communication_service.main.secondary_connection_string
  sensitive   = true
}

output "primary_key" {
  description = "Primary key for the Communication Services resource"
  value       = azurerm_communication_service.main.primary_key
  sensitive   = true
}

output "secondary_key" {
  description = "Secondary key for the Communication Services resource"
  value       = azurerm_communication_service.main.secondary_key
  sensitive   = true
}
