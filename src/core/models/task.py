import uuid
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import orm

from infrastructure.db.base import Model
from infrastructure.db.base import TimedMixin


class TaskLog(Model, TimedMixin):
    __tablename__ = "task_logs"

    id: orm.Mapped[UUID] = orm.mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
