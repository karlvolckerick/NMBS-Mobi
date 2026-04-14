from pathlib import Path

from fastapi import APIRouter
from starlette.responses import FileResponse

debugger_router = APIRouter(tags=["Debugger"])

static_path = Path(__file__).parent.parent / "static"


@debugger_router.get("/")
async def root() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")
