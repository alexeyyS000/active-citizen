import uuid
from datetime import time
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import and_
from sqlalchemy import orm
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.hybrid import hybrid_property

from core.models.task import TaskLog
from infrastructure.db.base import Model
from infrastructure.db.base import PublicKeyMixin
from infrastructure.db.base import RelationLoadingEnum
from infrastructure.db.base import TimedMixin
from infrastructure.db.utils.enums import AlertScheduleTypeEnum


class User(Model, TimedMixin, PublicKeyMixin):
    __tablename__ = "users"

    MAX_USERNAME_LENGTH = 64
    MAX_FIRST_NAME_LENGTH = 128
    MAX_LAST_NAME_LENGTH = 128
    MAX_LANGUAGE_CODE_LENGTH = 16

    id: orm.Mapped[UUID] = orm.mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tg_id: orm.Mapped[int] = orm.mapped_column(
        sa.BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )
    mos_ru_user_id: orm.Mapped[UUID] = orm.mapped_column(
        sa.ForeignKey("mos_ru_users.id", ondelete="CASCADE"),
        nullable=True,
    )
    username: orm.Mapped[str | None] = orm.mapped_column(
        sa.String(MAX_USERNAME_LENGTH),
        nullable=True,
    )
    first_name: orm.Mapped[str] = orm.mapped_column(
        sa.String(MAX_FIRST_NAME_LENGTH),
        nullable=False,
    )
    last_name: orm.Mapped[str | None] = orm.mapped_column(
        sa.String(MAX_LAST_NAME_LENGTH),
        nullable=True,
    )
    approved: orm.Mapped[bool] = orm.mapped_column(
        sa.Boolean,
        nullable=False,
        default=False,
    )
    admin: orm.Mapped[bool] = orm.mapped_column(
        sa.Boolean,
        nullable=False,
        default=False,
    )
    language_code: orm.Mapped[str | None] = orm.mapped_column(
        sa.String(MAX_LANGUAGE_CODE_LENGTH),
        nullable=True,
    )

    mos_ru_user = orm.relationship(
        "MosRuUser",
        info={"load": RelationLoadingEnum.JOINED},
    )

    @hybrid_property
    def full_name(self) -> str:
        full_name = self.first_name

        if self.last_name:
            full_name += " " + self.last_name

        return full_name

    @full_name.inplace.expression
    @classmethod
    def _full_name_expression(cls) -> sa.ColumnElement[str]:
        return sa.case(
            (cls.last_name != None, cls.first_name + " " + cls.last_name),  # noqa: E711
            else_=cls.first_name,
        )


class MosRuUser(Model, TimedMixin):
    __tablename__ = "mos_ru_users"

    MAX_LOGIN_LEN = 128
    MAX_PASSWORD_LEN = 256

    id: orm.Mapped[UUID] = orm.mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    login: orm.Mapped[str] = orm.mapped_column(
        sa.String(MAX_LOGIN_LEN),
        nullable=False,
    )
    password: orm.Mapped[str] = orm.mapped_column(
        sa.String(MAX_PASSWORD_LEN),
        nullable=False,
    )
    browser_state: orm.Mapped[dict] = orm.mapped_column(
        postgresql.JSON,
        nullable=True,
    )


class AlertSchedule(Model, TimedMixin):
    __tablename__ = "schedules"

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)

    user_id: orm.Mapped[UUID] = orm.mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    period: orm.Mapped[AlertScheduleTypeEnum] = orm.mapped_column(
        sa.Enum(AlertScheduleTypeEnum),
        nullable=False,
    )

    when: orm.Mapped[time] = orm.mapped_column(
        sa.Time(timezone=False),
        nullable=False,
    )

    task_log_id: orm.Mapped[UUID] = orm.mapped_column(
        sa.ForeignKey("task_logs.id", ondelete="CASCADE"),
        nullable=True,
    )

    task_log = orm.relationship(
        "TaskLog",
        primaryjoin=and_(task_log_id == TaskLog.id, TaskLog.deleted_at.is_(None)),
        info={"load": RelationLoadingEnum.JOINED},
    )
