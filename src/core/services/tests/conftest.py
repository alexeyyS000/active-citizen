import pytest

from core.dal.user import AlertScheduleDAL
from core.dal.user import UserDAL
from core.services.user import UserService
from infrastructure.db.utils.types import SessionFactory


@pytest.fixture()
def service_repo(user_dal: UserDAL, schedule_dal: AlertScheduleDAL):
    return UserService(user_dal, schedule_dal)


@pytest.fixture()
def user_dal(db_session_maker: SessionFactory):
    return UserDAL(db_session_maker)


@pytest.fixture()
def schedule_dal(db_session_maker: SessionFactory):
    return AlertScheduleDAL(db_session_maker)
