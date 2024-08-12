import enum


class PassStatusEnum(enum.IntEnum):
    PASSED = enum.auto()
    FAILED = enum.auto()


class ContentTypeEnum(enum.IntEnum):
    POLL = enum.auto()
    NOVELTY = enum.auto()
