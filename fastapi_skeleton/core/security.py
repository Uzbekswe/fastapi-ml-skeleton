import secrets

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from fastapi_skeleton.core.config import settings
from fastapi_skeleton.core.messages import AUTH_REQ, NO_API_KEY

api_key = APIKeyHeader(name="X-API-Key", auto_error=False)


def validate_request(header: str | None = Security(api_key)) -> None:
    if header is None:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail=NO_API_KEY
        )
    if not secrets.compare_digest(header, settings.API_KEY.get_secret_value()):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail=AUTH_REQ
        )
