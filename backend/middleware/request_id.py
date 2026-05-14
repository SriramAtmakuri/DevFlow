import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = uuid.uuid4().hex[:12]
        request.state.request_id = request_id

        start = time.perf_counter()
        with logger.contextualize(request_id=request_id):
            response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000)

        response.headers["X-Request-ID"] = request_id
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({elapsed_ms}ms)"
        )
        return response
