from fastapi import APIRouter, Request
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from fastapi_skeleton.models.heartbeat import HeartbeatResult

router = APIRouter()


@router.get(
    "/heartbeat",
    response_model=HeartbeatResult,
    name="heartbeat",
    responses={
        200: {
            "description": "Service is alive and model is loaded",
            "content": {
                "application/json": {"example": {"is_alive": True}}
            },
        },
        503: {
            "description": "Model not loaded",
            "content": {
                "application/json": {"example": {"is_alive": False}}
            },
        },
    },
)
def get_heartbeat(request: Request) -> HeartbeatResult:
    model_loaded = request.app.state.model is not None
    heartbeat = HeartbeatResult(is_alive=model_loaded)
    if not model_loaded:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            content=heartbeat.model_dump(),
        )
    return heartbeat
