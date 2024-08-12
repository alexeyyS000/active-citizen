from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import orm

from core import domains
from infrastructure.db.base import Model
from infrastructure.db.base import RelationLoadingEnum
from infrastructure.db.base import TimedMixin


class PassLog(Model, TimedMixin):
    __tablename__ = "pass_logs"

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    content_type: orm.Mapped[domains.ContentTypeEnum] = orm.mapped_column(
        sa.Enum(domains.ContentTypeEnum),
        nullable=False,
    )
    earned_points: orm.Mapped[int] = orm.mapped_column(
        sa.Integer,
        default=0,
        nullable=False,
    )
    object_id: orm.Mapped[int] = orm.mapped_column(
        sa.Integer,
        nullable=False,
    )
    status: orm.Mapped[domains.PassStatusEnum] = orm.mapped_column(
        sa.Enum(domains.PassStatusEnum),
        nullable=False,
    )
    user_id: orm.Mapped[UUID] = orm.mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    user = orm.relationship(
        "User",
        info={"load": RelationLoadingEnum.JOINED},
    )
