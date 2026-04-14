# Event Grid System Topic for ACS (for incoming call notifications)
resource "azurerm_eventgrid_system_topic" "acs" {
  name                = "${var.name}-events"
  resource_group_name = var.resource_group_name
  location            = "global"
  source_resource_id  = var.communication_services_id
  topic_type          = "Microsoft.Communication.CommunicationServices"
  tags                = var.tags
}

# Event Grid Subscription for incoming calls
resource "azurerm_eventgrid_event_subscription" "incoming_call" {
  count = var.webhook_endpoint != "" ? 1 : 0

  name  = "${var.name}-incoming-call"
  scope = var.communication_services_id

  webhook_endpoint {
    url                               = var.webhook_endpoint
    max_events_per_batch              = 1
    preferred_batch_size_in_kilobytes = 64
  }

  included_event_types = [
    "Microsoft.Communication.IncomingCall"
  ]

  retry_policy {
    max_delivery_attempts = 30
    event_time_to_live    = 1440
  }
}
