import abc


class BasePermission(abc.ABC):
    @abc.abstractmethod
    async def has_permission(self, **kwargs) -> bool:
        raise NotImplementedError

    async def __call__(self, **kwargs) -> bool:
        return await self.has_permission(**kwargs)

    def __and__(self, other: "BasePermission"):
        return AndBasePermission(self, other)

    def __or__(self, other: "BasePermission"):
        return OrBasePermission(self, other)

    def __invert__(self):
        return NotBasePermission(self)


class LogicBasePermission(BasePermission, abc.ABC):
    def __init__(self, *args):
        self.args = args


class AndBasePermission(LogicBasePermission):
    async def has_permission(self, **kwargs) -> bool:
        for perm in self.args:
            if not await perm.has_permission(**kwargs):
                return False
        return True


class OrBasePermission(LogicBasePermission):
    async def has_permission(self, **kwargs) -> bool:
        for perm in self.args:
            if await perm.has_permission(**kwargs):
                return True
        return False


class NotBasePermission(LogicBasePermission):
    async def has_permission(self, **kwargs) -> bool:
        perm = self.args[0]
        return not await perm.has_permission(**kwargs)
