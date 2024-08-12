import typing

import sqlalchemy as sa

from infrastructure.db.base import Model
from infrastructure.db.types import ModelType
from infrastructure.db.utils.dal.base import BaseSqlAlchemyRepository
from infrastructure.db.utils.types import AsyncSessionFactory
from utils.pagination import BaseAsyncPaginationCursor
from utils.pagination import BasePagination
from utils.pagination import PaginationPoint


class AsyncPaginationCursor(BaseAsyncPaginationCursor):
    # TODO: use base repository class
    def __init__(self, dal: "SqlAlchemyAsyncRepository", pagination: BasePagination) -> None:
        self._dal = dal
        self._pagination = pagination

    async def has_next(self) -> tuple[bool, int]:
        limit, offset = self._pagination.get_limit_offset()
        count = await self._dal.count()
        return offset < count, count

    # TODO: use correct typing for "items" argument
    async def next(self) -> tuple[PaginationPoint, typing.Iterable]:
        has_next, count = await self.has_next()
        point = PaginationPoint(count, has_next, self._pagination)

        if not has_next:
            return point, iter([])

        limit, offset = self._pagination.get_limit_offset()
        items: list[Model] = await self._dal.limit(limit).offset(offset).scalars()
        self._pagination.next()

        return point, items

    # TODO: use correct typing for "items" argument
    async def prev(self):
        raise NotImplementedError

    def __aiter__(self):
        return self

    async def __anext__(self) -> tuple[PaginationPoint, typing.Iterable]:
        point, items = await self.next()

        if not point.has_next:
            raise StopAsyncIteration

        return point, items


class SqlAlchemyAsyncRepository(BaseSqlAlchemyRepository):

    def __init__(self, session_factory: AsyncSessionFactory) -> None:
        self.session_factory = session_factory
        self._base_query: sa.Select = sa.select(self.Meta.model)

    async def first(self):
        async with self.session_factory() as session:
            res = await session.execute(self._base_query)
            return res.scalar_one_or_none()

    async def all(self) -> typing.Sequence[sa.Row]:
        async with self.session_factory() as session:
            res = await session.execute(self._base_query)
            return res.all()

    async def scalars(self) -> list[ModelType]:
        async with self.session_factory() as session:
            res = await session.execute(self._base_query)
            return list(res.scalars())

    def paginate(self, pagination: BasePagination) -> AsyncPaginationCursor:
        return AsyncPaginationCursor(self, pagination)

    async def count(self) -> int:
        async with self.session_factory() as session:
            subquery = self._base_query.limit(None).offset(None).subquery()
            count_query = sa.select(sa.func.count()).select_from(subquery)
            res = await session.execute(count_query)
            count = res.scalar()
            return typing.cast(int, count)

    # TODO: add return typing
    async def create_one(self, **kwargs):
        async with self.session_factory() as session:
            instance = self.Meta.model(**kwargs)
            session.add(instance)
            await session.commit()
            return instance

    # TODO: add return typing
    async def update_instance(self, instance, **kwargs):
        async with self.session_factory() as session:
            updated_instance = self._update(instance, **kwargs)
            await session.commit()
            return updated_instance

    # TODO: add return typing
    async def update_or_create(self, **kwargs) -> typing.Callable:
        async def update(**inner_kwargs):
            instance = await self.filter(**kwargs).first()

            if not instance:
                params = {**kwargs, **inner_kwargs}
                if self.pk and self.pk in params:
                    params.pop(self.pk)

                return await self.create_one(**params)

            instance = await self.update_instance(instance, **inner_kwargs)

            return instance

        return update

    async def get_or_create(self, **kwargs) -> tuple[ModelType, bool]:
        instance = await self.first()
        if instance:
            return instance, False

        await self.create_one(**kwargs)

        instance = await self.first()
        return instance, True

    # TODO: add return typing
    async def update(self, **kwargs):
        async with self.session_factory() as session:
            stmt = sa.update(self.Meta.model).values(**kwargs).returning(self.Meta.model)

            if self._base_query.whereclause is not None:
                stmt = stmt.where(self._base_query.whereclause)

            res = await session.execute(stmt)
            await session.commit()
            return res.scalar_one_or_none()
