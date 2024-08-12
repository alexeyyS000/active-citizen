from enum import Enum

import pydantic

from infrastructure.ag.api.schemas.base import BaseResponse
from infrastructure.ag.api.schemas.points import PointsResult


class NoveltyStatusEnum(Enum):
    ACTIVE = "active"
    PASSED = "passed"
    OLD = "old"


class NoveltiesFilterEnum(Enum):
    ACTIVE = "active"
    PASSED = "passed"
    OLD = "old"


class Novelty(pydantic.BaseModel):
    id: int
    points: int
    status: NoveltyStatusEnum
    begin_date: int
    end_date: int
    model_config = pydantic.ConfigDict(use_enum_values=True)


class NoveltiesSelectRequest(pydantic.BaseModel):
    count_per_page: int = pydantic.Field(description="Amount of polls per page")
    filter: list[NoveltiesFilterEnum] = pydantic.Field(description="Filters")
    page_number: int = pydantic.Field(description="Page number")
    model_config = pydantic.ConfigDict(use_enum_values=True)


class NoveltiesSelectResult(pydantic.BaseModel):
    last_page: bool = pydantic.Field(description="Is last page?")
    status: PointsResult | None = pydantic.Field(default=None, description="Status")
    novelties: list[Novelty] = pydantic.Field(description="Novelties")
    model_config = pydantic.ConfigDict(use_enum_values=True)


class NoveltyGetResult(pydantic.BaseModel):
    details: Novelty


class NoveltiesSelectResponse(BaseResponse):
    result: NoveltiesSelectResult | None


class NoveltyGetResponse(BaseResponse):
    result: NoveltyGetResult | None


class NoveltyGetRequest(pydantic.BaseModel):
    novelty_id: str
