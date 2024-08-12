import typing
from copy import copy
from datetime import datetime

import pytest

from core import dal
from core import domains
from core import models
from infrastructure.db.utils.types import SessionFactory
from infrastructure.tests.types import DBFactoryType
from utils.factory import FactoryMaker
from utils.math import unique_int

some_user = FactoryMaker(
    models.User,
    tg_id=unique_int,
    first_name="Michael",
    last_name="Smith",
    username="nickname",
)

some_pass_log = FactoryMaker(
    models.PassLog,
    content_type=domains.ContentTypeEnum.POLL,
    object_id=1,
    status=domains.PassStatusEnum.PASSED,
    earned_points=0,
    user=some_user,
)
one_passed = copy(some_pass_log)
one_failed = some_pass_log(status=domains.PassStatusEnum.FAILED)
one_passed_failed = one_failed & one_passed

one_10 = some_pass_log(earned_points=10)
one_20 = some_pass_log(earned_points=20)

curr = some_pass_log(created_at=datetime(2000, 1, 1, 1))
prev = some_pass_log(created_at=datetime(1999, 12, 1, 1))

curr_0 = curr(earned_points=0)
curr_10 = curr(earned_points=10)
prev_0 = prev(earned_points=0)
prev_10 = prev(earned_points=10)

curr_passed = curr(status=domains.PassStatusEnum.PASSED)
prev_passed = prev(status=domains.PassStatusEnum.PASSED)
curr_failed = curr(status=domains.PassStatusEnum.FAILED)
prev_failed = prev(status=domains.PassStatusEnum.FAILED)


@pytest.fixture()
def pass_log_repo(db_session_maker: SessionFactory) -> dal.PassLogDAL:
    return dal.PassLogDAL(db_session_maker)


@pytest.fixture()
def pass_log(db_factory: DBFactoryType) -> models.PassLog:
    pass_log = db_factory(some_pass_log)
    return typing.cast(models.PassLog, pass_log)


@pytest.fixture()
def user(db_factory: DBFactoryType) -> models.User:
    user = db_factory(some_user)
    return typing.cast(models.User, user)
