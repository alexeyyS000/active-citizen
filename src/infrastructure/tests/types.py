import typing

from infrastructure.db.types import ModelType
from utils.factory import FactoryMakerType

DBFactoryType = typing.Callable[[FactoryMakerType | None], ModelType | tuple[ModelType, ...] | None]
DBInstanceType = typing.Callable[[ModelType], tuple[ModelType, ...]]
