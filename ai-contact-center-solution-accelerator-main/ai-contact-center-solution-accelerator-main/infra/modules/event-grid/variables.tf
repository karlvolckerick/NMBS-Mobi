variable "name" {
  description = "Name prefix for Event Grid resources"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "communication_services_id" {
  description = "ID of the Azure Communication Services resource"
  type        = string
}

variable "webhook_endpoint" {
  description = "Webhook endpoint URL for incoming call notifications. Leave empty to skip subscription creation."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
