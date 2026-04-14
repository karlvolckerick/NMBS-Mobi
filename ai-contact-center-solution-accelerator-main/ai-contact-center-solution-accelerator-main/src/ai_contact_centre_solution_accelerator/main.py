import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from ai_contact_centre_solution_accelerator.config import get_config
from ai_contact_centre_solution_accelerator.core.mcp_loader import start_mcp_plugins, stop_mcp_plugins
from ai_contact_centre_solution_accelerator.routes.call import call_router
from ai_contact_centre_solution_accelerator.routes.config import config_router
from ai_contact_centre_solution_accelerator.routes.debugger import debugger_router
from ai_contact_centre_solution_accelerator.routes.health import health_router
from ai_contact_centre_solution_accelerator.routes.incoming import incoming_call_router

config = get_config()

# Configure logging
logging.basicConfig(
    level=config.server.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - start/stop MCP plugins."""
    await start_mcp_plugins(config)
    yield
    await stop_mcp_plugins()


app = FastAPI(
    title=config.app.name,
    description=config.app.description,
    version=config.app.version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(config_router)
app.include_router(debugger_router)
app.include_router(call_router)
app.include_router(incoming_call_router)

static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=static_path), name="static")

logger.info(f"Starting {config.app.name} v{config.app.description} in {config.app.version} mode")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
