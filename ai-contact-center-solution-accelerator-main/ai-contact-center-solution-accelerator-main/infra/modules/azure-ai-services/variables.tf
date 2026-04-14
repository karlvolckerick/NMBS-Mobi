variable "name" {
  description = "Name of the Azure AI Services resource"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for the AI Services resource"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "deployment_name" {
  description = "Name of the model deployment"
  type        = string
  default     = "gpt-4o-realtime"
}

variable "model_name" {
  description = "Name of the model to deploy"
  type        = string
  default     = "gpt-4o-realtime-preview"
}

variable "model_version" {
  description = "Version of the model to deploy"
  type        = string
  default     = "2024-12-17"
}

variable "model_capacity" {
  description = "Capacity (TPM in thousands) for the model deployment"
  type        = number
  default     = 100
}

# Transcribe model configuration
variable "transcribe_deployment_name" {
  description = "Name of the transcribe model deployment"
  type        = string
  default     = "gpt-4o-transcribe"
}

variable "transcribe_model_name" {
  description = "Name of the transcribe model to deploy"
  type        = string
  default     = "gpt-4o-transcribe"
}

variable "transcribe_model_version" {
  description = "Version of the transcribe model to deploy"
  type        = string
  default     = "2025-03-20"
}

variable "transcribe_model_capacity" {
  description = "Capacity (TPM in thousands) for the transcribe model deployment"
  type        = number
  default     = 100
}

# Chat model configuration (for eval module)
variable "chat_deployment_name" {
  description = "Name of the chat model deployment"
  type        = string
  default     = "gpt-4.1"
}

variable "chat_model_name" {
  description = "Name of the chat model to deploy"
  type        = string
  default     = "gpt-4.1"
}

variable "chat_model_version" {
  description = "Version of the chat model to deploy"
  type        = string
  default     = "2025-04-14"
}

variable "chat_model_capacity" {
  description = "Capacity (TPM in thousands) for the chat model deployment"
  type        = number
  default     = 100
}

# TTS model configuration (for eval module)
variable "tts_deployment_name" {
  description = "Name of the TTS model deployment"
  type        = string
  default     = "tts"
}

variable "tts_model_name" {
  description = "Name of the TTS model to deploy"
  type        = string
  default     = "tts"
}

variable "tts_model_version" {
  description = "Version of the TTS model to deploy"
  type        = string
  default     = "001"
}

variable "tts_model_capacity" {
  description = "Capacity (TPM in thousands) for the TTS model deployment"
  type        = number
  default     = 1
}

