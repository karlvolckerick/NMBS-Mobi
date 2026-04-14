resource "azurerm_ai_services" "main" {
  name                         = var.name
  location                     = var.location
  resource_group_name          = var.resource_group_name
  sku_name                     = "S0"
  custom_subdomain_name        = var.name
  local_authentication_enabled = false
  public_network_access        = "Enabled"

  identity {
    type = "SystemAssigned"
  }

  network_acls {
    default_action = "Allow"
  }

  tags = var.tags
}

resource "azurerm_cognitive_deployment" "realtime" {
  name                 = var.deployment_name
  cognitive_account_id = azurerm_ai_services.main.id

  model {
    format  = "OpenAI"
    name    = var.model_name
    version = var.model_version
  }

  sku {
    name     = "GlobalStandard"
    capacity = var.model_capacity
  }
}

resource "azurerm_cognitive_deployment" "transcribe" {
  name                 = var.transcribe_deployment_name
  cognitive_account_id = azurerm_ai_services.main.id

  model {
    format  = "OpenAI"
    name    = var.transcribe_model_name
    version = var.transcribe_model_version
  }

  sku {
    name     = "GlobalStandard"
    capacity = var.transcribe_model_capacity
  }

  depends_on = [azurerm_cognitive_deployment.realtime]
}

resource "azurerm_cognitive_deployment" "chat" {
  name                 = var.chat_deployment_name
  cognitive_account_id = azurerm_ai_services.main.id

  model {
    format  = "OpenAI"
    name    = var.chat_model_name
    version = var.chat_model_version
  }

  sku {
    name     = "GlobalStandard"
    capacity = var.chat_model_capacity
  }

  depends_on = [azurerm_cognitive_deployment.transcribe]
}

resource "azurerm_cognitive_deployment" "tts" {
  name                 = var.tts_deployment_name
  cognitive_account_id = azurerm_ai_services.main.id

  model {
    format  = "OpenAI"
    name    = var.tts_model_name
    version = var.tts_model_version
  }

  sku {
    name     = "Standard"
    capacity = var.tts_model_capacity
  }

  depends_on = [azurerm_cognitive_deployment.chat]
}

