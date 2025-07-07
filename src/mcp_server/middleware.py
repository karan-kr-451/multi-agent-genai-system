from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from typing import Callable
from src.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def auth_middleware(request: Request, call_next: Callable):
    """
    Middleware to handle API key authentication.
    Skips authentication if ENABLE_AUTH is False.
    """
    if not settings.ENABLE_AUTH:
        return await call_next(request)

    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required"
        )
    
    if api_key != settings.API_KEY:
        logger.warning("Invalid API key attempt from %s", request.client.host)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return await call_next(request)

async def error_handling_middleware(request: Request, call_next: Callable):
    """
    Middleware to handle errors consistently across the application.
    Logs errors and returns standardized error responses.
    """
    try:
        return await call_next(request)
        
    except HTTPException as exc:
        # Re-raise FastAPI's HTTPExceptions as they're already handled properly
        raise
        
    except Exception as exc:
        # Log unexpected errors
        logger.error(
            "Unhandled error processing request %s %s: %s",
            request.method,
            request.url.path,
            str(exc),
            exc_info=True
        )
        
        # Return a generic error response in production
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred. Please try again later."
            }
        )

async def request_logging_middleware(request: Request, call_next: Callable):
    """
    Middleware to log all incoming requests and their processing time.
    """
    import time
    
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request started: %s %s from %s",
        request.method,
        request.url.path,
        request.client.host
    )
    
    response = await call_next(request)
    
    # Log response
    process_time = (time.time() - start_time) * 1000
    status_code = response.status_code
    logger.info(
        "Request completed: %s %s - Status: %d - Duration: %.2fms",
        request.method,
        request.url.path,
        status_code,
        process_time
    )
    
    return response