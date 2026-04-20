"""FastAPI application entry point"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers.summarize import router
from app.utils.exceptions import AppError
from app.schemas.error import ErrorDetail


def create_app() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title="Image Summarizer API",
        description="API for extracting text from images and generating summaries",
        version="1.0.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handler for AppError
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                }
            },
        )

    # Include routers
    app.include_router(router)

    return app


app = create_app()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}