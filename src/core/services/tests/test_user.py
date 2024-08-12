import pytest

from core.dal.user import AlertScheduleDAL
from core.services.user import UserService
from infrastructure.db.utils.enums import AlertScheduleTypeEnum


@pytest.fixture()
def create_one_user(service_repo: UserService):

    test_data = dict(
        tg_id=1,
        first_name="first_name",
        last_name="last_name",
        username="username",
        language_code="EN",
    )

    return test_data


def test_get_one_not_exist(schedule_dal: AlertScheduleDAL, service_repo):

    test_data = dict(
        tg_id=1,
        first_name="first_name",
        last_name="last_name",
        username="username",
        language_code="EN",
    )

    user, created = service_repo.get_or_create(test_data, tg_id=test_data["tg_id"])#TODO service
    schedule_monthly = schedule_dal.filter(user_id=user.id, period=AlertScheduleTypeEnum.MONTHLY).first()
    assert created
    assert schedule_monthly is not None


def test_get_one_exist(schedule_dal: AlertScheduleDAL, service_repo):

    test_data = dict(
        tg_id=1,
        first_name="first_name",
        last_name="last_name",
        username="username",
        language_code="EN",
    )

    user, created = service_repo.get_or_create(test_data, tg_id=test_data["tg_id"])#TODO service
    schedule_monthly = schedule_dal.filter(user_id=user.id, period=AlertScheduleTypeEnum.MONTHLY).first()
    assert not created
    assert schedule_monthly is not None