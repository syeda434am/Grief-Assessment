import time, logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from com.mhire.app.common.network_responses import (NetworkResponse, HTTPCode)
from com.mhire.app.services.schedule_builder.schedule_builder_router import router as schedule_builder_router 
from com.mhire.app.services.sentiment_toolkit.sentiment_toolkit_router import router as sentiment_toolkit_router
from com.mhire.app.services.personalized_content.personalized_content_router import router as personalized_content_router 

# Configure logging with proper format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Initialize FastAPI app
app = FastAPI(
    title="Grief Counseling AI",
    description="An AI-powered platform for personalized grief counseling and support",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(schedule_builder_router)
app.include_router(sentiment_toolkit_router)
app.include_router(personalized_content_router)

# Health check endpoint
@app.get("/health", response_class=JSONResponse)
async def health_check(http_request: Request):
    """Health check endpoint"""
    start_time = time.time()
    return NetworkResponse().success_response(
        http_code=HTTPCode.SUCCESS,
        message="Health check successful",
        data={
            "status": "healthy",
            "message": "Grief Counseling AI is running and healthy"
        },
        resource=http_request.url.path,
        duration=start_time
    )

# Root endpoint
@app.get("/", response_class=JSONResponse)
async def root(http_request: Request):
    """Root endpoint"""
    start_time = time.time()
    return NetworkResponse().success_response(
        http_code=HTTPCode.SUCCESS,
        message="Root endpoint data",
        data={
            "name": "Grief Counseling AI",
            "version": "1.0.0",
            "description": "Grief Counseling AI Platform",
        },
        resource=http_request.url.path,
        duration=start_time
    )

