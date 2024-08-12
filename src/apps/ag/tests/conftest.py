import typing

import pytest

from core import models
from infrastructure.ag.web.client import AgWebClient
from infrastructure.tests.types import DBFactoryType
from utils.factory import FactoryMaker

some_mos_ru_user = FactoryMaker(  # noqa: S106
    models.MosRuUser,
    login="user",
    password="secret-password",
)


@pytest.fixture()
def ag_web_client():
    ag_web_client = AgWebClient(headless=True)
    with ag_web_client as client:
        yield client


@pytest.fixture()
def mos_ru_user(db_factory: DBFactoryType) -> models.MosRuUser:
    instance = db_factory(some_mos_ru_user)
    return typing.cast(models.MosRuUser, instance)
