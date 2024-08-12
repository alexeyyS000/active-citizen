import typing

import sqlalchemy as sa

from infrastructure.db.base import Model
from infrastructure.db.types import ModelType
from infrastructure.db.utils.dal.base import BaseSqlAlchemyRepository
from infrastructure.db.utils.types import SessionFactory
from utils.pagination import BasePagination
from utils.pagination import BasePaginationCursor
from utils.pagination import PaginationPoint


class PaginationCursor(BasePaginationCursor):
    # TODO: use base repository class
    def __init__(self, dal: "SqlAlchemyRepository", pagination: BasePagination) -> None:
        self._dal = dal
        self._pagination = pagination

    def has_next(self) -> tuple[bool, int]:
        limit, offset = self._pagination.get_limit_offset()
        count = self._dal.count()
        return offset < count, count

    # TODO: use correct typing for "items" argument
    def next(self) -> tuple[PaginationPoint, typing.Iterable]:
        has_next, count = self.has_next()
        point = PaginationPoint(count, has_next, self._pagination)

        if not has_next:
            return point, iter([])

        limit, offset = self._pagination.get_limit_offset()
        items: list[Model] = self._dal.limit(limit).offset(offset).scalars()
        self._pagination.next()

        return point, items

    # TODO: use correct typing for "items" argument
    async def prev(self):
        raise NotImplementedError

    def __iter__(self):
        return self

    def __next__(self) -> tuple[PaginationPoint, typing.Iterable]:
        point, items = self.next()

        if not point.has_next:
            raise StopIteration

        return point, items


class SqlAlchemyRepository(BaseSqlAlchemyRepository):

    def __init__(self, session_factory: SessionFactory) -> None:
        self.session_factory = session_factory
        self._base_query: sa.Select = sa.select(self.Meta.model)

    def first(self):
        with self.session_factory() as session:
            return session.execute(self._base_query).scalar_one_or_none()

    def all(self) -> typing.Sequence[sa.Row]:
        with self.session_factory() as session:
            return session.execute(self._base_query).all()

    def scalars(self) -> list[ModelType]:
        with self.session_factory() as session:
            res = session.execute(self._base_query)
            return list(res.scalars())

    def paginate(self, pagination: BasePagination) -> PaginationCursor:
        return PaginationCursor(self, pagination)

    def count(self) -> int:
        with self.session_factory() as session:
            subquery = self._base_query.limit(None).offset(None).subquery()
            count_query = sa.select(sa.func.count()).select_from(subquery)
            res = session.execute(count_query)
            count = res.scalar()
            return typing.cast(int, count)

    def create_one(self, **kwargs):
        with self.session_factory() as session:
            instance = self.Meta.model(**kwargs)
            session.add(instance)
            session.commit()
            return instance

    def update_instance(self, instance, **kwargs):
        with self.session_factory() as session:
            updated_instance = self._update(instance, **kwargs)
            session.commit()
            return updated_instance

    def update_or_create(self, **kwargs) -> typing.Callable:
        def update(**inner_kwargs):
            instance = self.filter(**kwargs).first()

            if not instance:
                params = {**kwargs, **inner_kwargs}
                if self.pk and self.pk in params:
                    params.pop(self.pk)
                return self.create_one(**params)

            instance = self.update_instance(instance, **inner_kwargs)

            return instance

        return update

    def get_or_create(self, **kwargs) -> tuple[ModelType, bool]:
        instance = self.first()
        if instance:
            return instance, False

        self.create_one(**kwargs)

        instance = self.first()
        return instance, True

    def update(self, **kwargs):
        with self.session_factory() as session:
            stmt = sa.update(self.Meta.model).values(**kwargs).returning(self.Meta.model)

            if self._base_query.whereclause is not None:
                stmt = stmt.where(self._base_query.whereclause)

            res = session.execute(stmt)
            session.commit()
            return res.scalar_one_or_none()
