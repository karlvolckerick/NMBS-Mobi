output "system_topic_id" {
  description = "ID of the Event Grid System Topic"
  value       = azurerm_eventgrid_system_topic.acs.id
}

output "system_topic_name" {
  description = "Name of the Event Grid System Topic"
  value       = azurerm_eventgrid_system_topic.acs.name
}

output "subscription_id" {
  description = "ID of the Event Grid Subscription (null if webhook_endpoint not set)"
  value       = var.webhook_endpoint != "" ? azurerm_eventgrid_event_subscription.incoming_call[0].id : null
}

output "subscription_name" {
  description = "Name of the Event Grid Subscription (null if webhook_endpoint not set)"
  value       = var.webhook_endpoint != "" ? azurerm_eventgrid_event_subscription.incoming_call[0].name : null
}
