
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_504_GATEWAY_TIMEOUT
import asyncio

class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Return gateway timeout error (504)
    if the request processing time is above a certain threshold
    """
    def __init__(self, app, timeout: int = 10):
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(self, request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.timeout)
        except asyncio.TimeoutError:
            return JSONResponse(
                {"detail": "Request timed out"}, status_code=HTTP_504_GATEWAY_TIMEOUT
            )