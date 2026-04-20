from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Error detail"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")


class ErrorResponse(BaseModel):
    """Error response"""
    error: ErrorDetail = Field(..., description="Error detail")