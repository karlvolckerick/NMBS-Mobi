import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from ai_contact_centre_solution_accelerator.config import Config, get_config

logger = logging.getLogger(__name__)

config_router = APIRouter(tags=["Config"])


@config_router.get("/config")
async def config_json(config: Annotated[Config, Depends(get_config)]):
    """Returns JSON representation of the current configuration."""
    return config.model_dump()
