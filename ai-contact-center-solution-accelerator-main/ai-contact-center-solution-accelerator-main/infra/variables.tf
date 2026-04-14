variable "project_name" {
  description = "Name of the project, used as prefix for all resources"
  type        = string
  default     = "ai-contact-centre"
}

variable "subscription_id" {
  description = "Azure subscription ID (defaults to current az cli subscription)"
  type        = string
  default     = null
}


variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "swedencentral"
}

variable "openai_location" {
  description = "Azure region for AI Services resources (may differ from main location due to model availability)"
  type        = string
  default     = "swedencentral"
}

variable "acs_data_location" {
  description = "Data location for Azure Communication Services (e.g., United States, Europe, UK, Australia, Japan)"
  type        = string
  default     = "Europe"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "dev"
    Project     = "ai-contact-centre"
    ManagedBy   = "terraform"
  }
}

# AI Services Model Configuration
variable "openai_deployment_name" {
  description = "Name of the OpenAI deployment"
  type        = string
  default     = "gpt-4o-realtime"
}

variable "openai_model_name" {
  description = "Name of the OpenAI model to deploy"
  type        = string
  default     = "gpt-4o-realtime-preview"
}

variable "openai_model_version" {
  description = "Version of the OpenAI model"
  type        = string
  default     = "2024-12-17"
}

variable "openai_model_capacity" {
  description = "Capacity (TPM in thousands) for the OpenAI deployment"
  type        = number
  default     = 100
}

# Transcribe Model Configuration
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
  description = "Version of the transcribe model"
  type        = string
  default     = "2025-03-20"
}

variable "transcribe_model_capacity" {
  description = "Capacity (TPM in thousands) for the transcribe deployment"
  type        = number
  default     = 100
}

# Chat Model Configuration (for eval module)
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
  description = "Version of the chat model"
  type        = string
  default     = "2025-04-14"
}

variable "chat_model_capacity" {
  description = "Capacity (TPM in thousands) for the chat deployment"
  type        = number
  default     = 100
}

# TTS Model Configuration (for eval module)
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
  description = "Version of the TTS model"
  type        = string
  default     = "001"
}

variable "tts_model_capacity" {
  description = "Capacity (TPM in thousands) for the TTS deployment"
  type        = number
  default     = 1
}

# ACS Event Grid Configuration
variable "acs_webhook_endpoint" {
  description = "Webhook endpoint URL for ACS incoming call notifications (e.g., https://your-app.azurecontainerapps.io/api/calls/incoming). Leave empty to skip Event Grid subscription creation."
  type        = string
  default     = ""
}

