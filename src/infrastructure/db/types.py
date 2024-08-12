from typing import TypeVar

from infrastructure.db.base import Model

ModelType = TypeVar("ModelType", bound=Model)
