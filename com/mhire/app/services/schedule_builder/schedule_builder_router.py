import logging
import time
from fastapi import APIRouter, Request, HTTPException

from com.mhire.app.services.schedule_builder.schedule_builder import ScheduleBuilder
from com.mhire.app.services.schedule_builder.schedule_builder_schema import ScheduleRequest, DailySchedule
from com.mhire.app.common.network_responses import NetworkResponse, HTTPCode, ErrorCode, Message

logger = logging.getLogger(__name__)

router = APIRouter()
schedule_builder = ScheduleBuilder()
response = NetworkResponse()

@router.post("/api/v1/daily-schedule")
async def get_daily_schedule(request: ScheduleRequest, http_request: Request):
    """Generate a personalized daily schedule based on user input"""
    start_time = time.time()
    
    try:
        schedule_result = await schedule_builder.generate_daily_schedule(request)
        return response.success_response(
            http_code=HTTPCode.SUCCESS,
            message=Message.SuccessMessage.RESPONSE_GENERATED,
            data=schedule_result.model_dump(),
            resource=http_request.url.path,
            duration=time.time() - start_time
        )
    
    except HTTPException as http_e:
        logger.error(f"Business logic error: {str(http_e.detail)}")
        return response.json_response(
            http_code=http_e.status_code,
            error_code=ErrorCode.UnprocessableEntity.CONTEXT_PROCESSING_ERROR,
            error_message=str(http_e.detail),
            resource=http_request.url.path,
            duration=time.time() - start_time
        )
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return response.json_response(
            http_code=HTTPCode.INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.InternalServerError.INTERNAL_SERVER_ERROR,
            error_message=Message.ErrorMessage.InternalServerError.INTERNAL_SERVER_ERROR,
            resource=http_request.url.path,
            duration=time.time() - start_time
        )