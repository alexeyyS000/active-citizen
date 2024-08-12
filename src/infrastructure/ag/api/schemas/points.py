from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from infrastructure.ag.api.schemas.base import BaseResponse


class PointsResult(BaseModel):
    all_points: int = Field(description="All points")
    current_points: int = Field(description="Current points")
    freezed_points: int = Field(description="Freeze points")
    spent_points: int = Field(description="Spent points")
    state: str | None = Field(description="State", default=None)


class PointsGetResponse(BaseResponse):
    result: PointsResult | None
    model_config = ConfigDict(use_enum_values=True)
