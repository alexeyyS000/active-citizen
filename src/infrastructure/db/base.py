"""
Database Model base class.
"""

import enum
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

convention = {
    "ix": "ix_%(column_0_label)s",  # INDEX
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",  # UNIQUE
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # CHECK
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",  # FOREIGN KEY
    "pk": "pk_%(table_name)s",  # PRIMARY KEY
}

mapper_registry = orm.registry(metadata=sa.MetaData(naming_convention=convention))


class Model(orm.DeclarativeBase):
    registry = mapper_registry
    metadata = mapper_registry.metadata


class TimedMixin:
    """
    A mixin that adds created_at, updated_at, deleted_at timestamp fields to the model.
    """

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    updated_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )
    deleted_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )


class PublicKeyMixin:
    """
    A mixin that adds public_id fields to the model.
    """

    # public_id: orm.Mapped[int] = orm.mapped_column(
    #     sa.BigInteger,
    #     transaction_public_id_seq,
    #     server_default=transaction_public_id_seq.next_value(),
    #     nullable=False,
    #     unique=True,
    # )


class RelationLoadingEnum(str, enum.Enum):
    JOINED = "joined"
    SELECTIN = "selectin"
    SUBQUERY = "subquery"
