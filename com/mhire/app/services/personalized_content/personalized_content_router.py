import logging
import time

from fastapi import APIRouter, Request

from com.mhire.app.services.personalized_content.personalized_content import PersonalizedContent
from com.mhire.app.services.personalized_content.personalized_content_schema import GriefContentRequest, GriefContentResponse
from com.mhire.app.common.network_responses import NetworkResponse, HTTPCode, ErrorCode, Message

logger = logging.getLogger(__name__)

router = APIRouter()
personalized_content = PersonalizedContent()
response = NetworkResponse()

@router.post("/api/v1/personalized-content", response_model=GriefContentResponse)
async def get_personalized_content(request: GriefContentRequest, http_request: Request):
    """Generate personalized grief content based on user input"""
    start_time = time.time()
    
    try:
        content_result = await personalized_content.generate_personalized_content(request)
        return response.success_response(
            http_code=HTTPCode.SUCCESS,
            message=Message.SuccessMessage.RESPONSE_GENERATED,
            data=content_result,
            resource=http_request.url.path,
            duration=time.time() - start_time
        )
    
    except Exception as e:
        return response.json_response(
            http_code=HTTPCode.UNPROCESSABLE_ENTITY,
            error_code=ErrorCode.UnprocessableEntity.CONTEXT_PROCESSING_ERROR,
            error_message=f"{Message.ErrorMessage.UnprocessableEntity.CONTEXT_PROCESSING_ERROR}",
            resource=http_request.url.path,
            duration=time.time() - start_time
        )