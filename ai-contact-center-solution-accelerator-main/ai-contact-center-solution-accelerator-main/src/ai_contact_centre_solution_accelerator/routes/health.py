import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

health_router = APIRouter(tags=["Health"])


@health_router.get("/status")
async def status() -> str:
    logger.info("Status probe called")
    return "OK"
