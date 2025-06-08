import logging
import time

from fastapi import APIRouter, Request

from com.mhire.app.services.sentiment_toolkit.sentiment_toolkit import SentimentToolkit
from com.mhire.app.services.sentiment_toolkit.sentiment_toolkit_schema import UserInput, ToolsResponse
from com.mhire.app.common.network_responses import NetworkResponse, HTTPCode, ErrorCode, Message

logger = logging.getLogger(__name__)

router = APIRouter()
sentiment_toolkit = SentimentToolkit()
response = NetworkResponse()

@router.post("/api/v1/sentiment-analyze", response_model=ToolsResponse)
async def analyze_sentiment(request: UserInput, http_request: Request):
    """
    Analyze grief input and provide personalized tool recommendations with sentiment analysis.
    """
    start_time = time.time()
    
    try:
        analysis_result = await sentiment_toolkit.analyze_grief(request)
        return response.success_response(
            http_code=HTTPCode.SUCCESS,
            message=Message.SuccessMessage.RESPONSE_GENERATED,
            data=analysis_result,
            resource=http_request.url.path,
            duration=time.time() - start_time
        )
    
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}", exc_info=True)
        return response.json_response(
            http_code=HTTPCode.UNPROCESSABLE_ENTITY,
            error_code=ErrorCode.UnprocessableEntity.CONTEXT_PROCESSING_ERROR,
            error_message=f"{Message.ErrorMessage.UnprocessableEntity.CONTEXT_PROCESSING_ERROR}",
            resource=http_request.url.path,
            duration=time.time() - start_time
        )