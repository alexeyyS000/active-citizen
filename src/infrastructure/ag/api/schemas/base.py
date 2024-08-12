"""
Base AG API schemas
"""

from pydantic import AnyHttpUrl
from pydantic import BaseModel
from pydantic import Field


class BaseResponse(BaseModel):
    error_code: int = Field(description="Error code", alias="errorCode")
    error_message: str = Field(description="Error code", alias="errorMessage")
    exec_time: float | None = Field(default=None, description="Execution time", alias="execTime")
    request_id: str | None = Field(default=None, description="Request ID (UUID 4)", alias="requestId")


class Voter(BaseModel):
    id: int
    image_url: AnyHttpUrl
