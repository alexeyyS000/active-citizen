"""
RPA exceptions.
"""


class BasePageError(Exception):
    pass


class _PageNotFoundError(BasePageError):
    pass
