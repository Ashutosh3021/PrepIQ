from fastapi import HTTPException, status
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
import logging

logger = logging.getLogger(__name__)

class RequestSizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_size: int = 10 * 1024 * 1024):  # 10MB default
        self.app = app
        self.max_size = max_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create a temporary request to check headers
        try:
            request = Request(scope)
            
            # Check Content-Length header if present
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    content_length = int(content_length)
                    if content_length > self.max_size:
                        # Return a proper error response instead of raising exception
                        async def send_error_response():
                            response_headers = [
                                (b"content-type", b"application/json"),
                                (b"content-length", b"128")
                            ]
                            await send({
                                "type": "http.response.start",
                                "status": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                "headers": response_headers
                            })
                            error_body = f"{{\"detail\": \"Request size too large: {content_length} bytes. Maximum allowed: {self.max_size} bytes\"}}".encode("utf-8")
                            await send({
                                "type": "http.response.body",
                                "body": error_body,
                                "more_body": False
                            })
                        await send_error_response()
                        return
                except ValueError:
                    # If content-length header is malformed, log and continue
                    logger.warning(f"Invalid Content-Length header: {content_length}")
                    pass
            
            # Proceed with the request
            await self.app(scope, receive, send)
        except Exception as e:
            logger.error(f"Error in RequestSizeLimitMiddleware: {e}")
            # If there's an error in our middleware, pass to the next app
            await self.app(scope, receive, send)