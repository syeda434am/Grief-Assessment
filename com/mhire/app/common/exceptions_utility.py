import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def rethrow_as_http_exception(exc: Exception):
    """Rethrows an exception as HTTPException with raw message and status code if available."""
    
    # Extract status code if available
    status_code = getattr(exc, "status_code", None)
    if not status_code and hasattr(exc, "response") and hasattr(exc.response, "status_code"):
        status_code = exc.response.status_code

    status_code = status_code if status_code else 500

    # Extract error detail
    detail = str(getattr(exc, "detail", exc))

    # Log the actual error before raising HTTPException
    logger.error(f"Rethrowing exception: status_code={status_code}, detail={detail}")

    raise HTTPException(
        status_code=status_code,
        detail=detail
    )
