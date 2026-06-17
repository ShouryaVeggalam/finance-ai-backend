from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import CelestraError


async def celestra_exception_handler(_request: Request, exc: CelestraError) -> JSONResponse:
    status_map = {
        "NOT_FOUND": 404,
        "UNAUTHORIZED": 401,
        "FORBIDDEN": 403,
        "VALIDATION_ERROR": 422,
        "CONFLICT": 409,
    }
    return JSONResponse(
        status_code=status_map.get(exc.code, 400),
        content={"error": exc.code, "message": exc.message},
    )
