import dotenv
dotenv.load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.v1 import api_router
from core.config import settings
from core.events import create_start_app_handler, create_stop_app_handler

def get_application():
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Content Management System API",
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_event_handler("startup", create_start_app_handler())
    app.add_event_handler("shutdown", create_stop_app_handler())

    app.include_router(api_router, prefix=settings.API_V1_STR)
    # app.mount("/static", StaticFiles(directory="static"), name="static")

    return app

app = get_application()

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions with proper error formatting"""
    return {
        "error": {
            "code": exc.status_code,
            "message": exc.detail,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    return {
        "error": {
            "code": 500,
            "message": "Internal server error",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }