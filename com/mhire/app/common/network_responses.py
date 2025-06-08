from typing import Dict, Any
from fastapi.responses import JSONResponse

class NetworkResponse:

    def __init__(self, version=0.1):
        self.version = version

    def success_response(
        self, http_code: int, message: str, data: Dict[str, Any], resource: str, duration: float
    ) -> JSONResponse:
        return JSONResponse(
            status_code=http_code,
            content={
                "success": True,
                "message": message,
                "data": data,  # Direct data without serialization
                "resource": resource,
                "duration": f"{duration}s"
            }
        )

    def json_response(
        self, http_code: int, error_code: int, error_message: str, resource: str, duration: float
    ) -> JSONResponse:
        return JSONResponse(
            status_code=http_code,
            content={
                "code": http_code,
                "success": False,
                "error": {
                    "code": error_code,
                    "message": error_message
                },
                "resource": resource,
                "duration": f"{duration}s"
            }
        )

class HTTPCode:
    SUCCESS = 200
    BAD_REQUEST = 400
    FORBIDDEN = 403
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500

class ErrorCode:
    class BadRequest:
        EMPTY_MESSAGE = 40001
        MESSAGE_TOO_LONG = 40002
        INVALID_MESSAGE_FORMAT = 40003
        
    class Forbidden:
        BLOCKED_CONTENT = 40301
        INAPPROPRIATE_CONTENT = 40302

    class UnprocessableEntity:
        INVALID_CONTENT = 42213
        CONTEXT_PROCESSING_ERROR = 42202

    class InternalServerError:
        UNEXPECTED_ERROR = 50001
        MODEL_UNAVAILABLE = 50002
        RESPONSE_GENERATION_FAILED = 50003
        CONTEXT_RETRIEVAL_ERROR = 50004
        INTERNAL_SERVER_ERROR = 50005

class Message:
    class SuccessMessage:
        RESPONSE_GENERATED = "Response generated successfully."

    class ErrorMessage:
        class BadRequest:
            EMPTY_MESSAGE = "Message cannot be empty."
            MESSAGE_TOO_LONG = "Message exceeds maximum length limit."
            INVALID_MESSAGE_FORMAT = "Invalid message format."

        class Forbidden:
            BLOCKED_CONTENT = "Content has been blocked by content filter."
            INAPPROPRIATE_CONTENT = "Inappropriate content detected."

        class UnprocessableEntity:
            INVALID_MESSAGE_FORMAT = "The message format is not supported."
            CONTEXT_PROCESSING_ERROR = "Error processing grief content."

        class InternalServerError:
            UNEXPECTED_ERROR = "An unexpected error occurred."
            MODEL_UNAVAILABLE = "AI model is currently unavailable."
            RESPONSE_GENERATION_FAILED = "Failed to generate response."
            CONTEXT_RETRIEVAL_ERROR = "Error retrieving conversation context."
            INTERNAL_SERVER_ERROR = "Internal server error occurred."