"""
Utilities for creating factories.
"""

import typing

FactoryMakerType = typing.Union["FactoryMaker", "FactoryGroupMaker"]


class FactoryGroupMaker:
    def __init__(self, *args):
        self.args = args

    def __and__(self, other: FactoryMakerType) -> "FactoryGroupMaker":
        if isinstance(other, FactoryMaker):
            return self.__class__(other, *self.args)
        elif isinstance(other, FactoryGroupMaker):
            return self.__class__(*other.args, *self.args)

    def make(self) -> typing.Iterable[typing.Any]:
        return (factory_maker.make() for factory_maker in self.args)


class FactoryMaker:
    def __init__(self, factory: typing.Callable[..., typing.Any], **kwargs) -> None:
        self.factory = factory
        self.kwargs = kwargs

    def __and__(self, other: "FactoryMaker") -> "FactoryGroupMaker":
        return FactoryGroupMaker(self, other)

    def __call__(self, *args, **kwargs) -> "FactoryMaker":
        """
        Merge factory maker arguments.
        """
        return self.__class__(self.factory, **(self.kwargs | kwargs))

    @staticmethod
    def _calc_value(arg_value: typing.Any) -> typing.Any:
        if isinstance(arg_value, FactoryMaker):
            return arg_value.make()
        elif callable(arg_value):
            return arg_value()
        else:
            return arg_value

    def make(self) -> typing.Any:
        kwargs = {arg_name: self._calc_value(arg_value) for arg_name, arg_value in self.kwargs.items()}
        return self.factory(**kwargs)
