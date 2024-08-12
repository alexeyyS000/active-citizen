from datetime import datetime
from enum import Enum

import pydantic

from infrastructure.ag.api.schemas.base import BaseResponse
from infrastructure.ag.api.schemas.base import Voter


class Variant(pydantic.BaseModel):
    id: int = pydantic.Field(description="Answer ID")


class QuestionTypeEnum(Enum):
    RADIO_BUTTON = "radiobutton"
    CHECKBOX = "checkbox"


class Question(pydantic.BaseModel):
    id: int = pydantic.Field(description="Question ID")
    question: str = pydantic.Field(description="Question text")
    type: QuestionTypeEnum = pydantic.Field(description="Question Type")
    variants: list[Variant]


class PollsFilterEnum(str, Enum):
    AVAILABLE = "available"
    ACTIVE = "active"
    PASSED = "passed"
    OLD = "old"


class PollKindEnum(str, Enum):
    STANDART = "standart"
    QUIZ = "quiz"
    GROUP = "group"


class PollStatusEnum(str, Enum):
    ACTIVE = "active"
    PASSED = "passed"
    OLD = "old"


class PollsSelectRequest(pydantic.BaseModel):
    count_per_page: int = pydantic.Field(description="Amount of polls per page")
    filters: list[PollsFilterEnum] = pydantic.Field(description="Filters")
    page_number: int = pydantic.Field(description="Page number")
    categories: list[int] = pydantic.Field(description="Categories")
    parent_id: int | None = pydantic.Field(None, description="Parent Poll ID")


class Poll(pydantic.BaseModel):
    id: int = pydantic.Field(description="ID")
    title: str = pydantic.Field(description="Poll title")
    begin_date: datetime = pydantic.Field(description="Begin date (unix timestamp)")
    end_date: datetime = pydantic.Field(description="End date (unix timestamp)")
    days_remaining: int = pydantic.Field(description="Days remaining")
    has_results: bool = pydantic.Field(description="Has results")
    image: pydantic.AnyHttpUrl | None = pydantic.Field(description="Image URL", default=None)
    is_hot: bool = pydantic.Field(description="")  # TODO: Find appropriate description
    kind: PollKindEnum = pydantic.Field(description="Poll kind")
    points: int = pydantic.Field(description="Points")
    show_poll_stats: bool = pydantic.Field(description="Show poll stats predictor")
    status: PollStatusEnum = pydantic.Field(description="Poll status")
    thumbnail: pydantic.AnyHttpUrl | None = pydantic.Field(description="Thumbnail image URL", default=None)
    voters_count: int = pydantic.Field(description="Voters count")


class PollsSelectResult(pydantic.BaseModel):
    last_page: bool = pydantic.Field(description="Is last page?")
    categories: list[int] = pydantic.Field(description="Categories")
    polls: list[Poll] = pydantic.Field(description="Polls")


class PollsSelectResponse(BaseResponse):
    model_config = pydantic.ConfigDict(use_enum_values=True)

    result: PollsSelectResult | None


class PollGetRequest(pydantic.BaseModel):
    poll_id: int


class PollGetDetails(Poll):
    last_voters: list[Voter] = pydantic.Field(description="Last voters", default_factory=list)
    album_images: list = pydantic.Field(description="Album images", default_factory=list)


class PollGetResult(pydantic.BaseModel):
    details: PollGetDetails
    experts: list  # TODO: add details
    questions: list[Question]


class PollGetResponse(BaseResponse):
    result: PollGetResult | None
