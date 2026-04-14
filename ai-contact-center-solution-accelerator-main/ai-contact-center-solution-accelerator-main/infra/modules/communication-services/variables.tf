variable "name" {
  description = "Name of the Azure Communication Services resource"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "data_location" {
  description = "Data location for the Communication Services resource (e.g., United States, Europe, UK, Australia, Japan, Singapore, Brazil)"
  type        = string
  default     = "Europe"
}

variable "tags" {
  description = "Tags to apply to the resource"
  type        = map(string)
  default     = {}
}
