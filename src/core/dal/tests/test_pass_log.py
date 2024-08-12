from datetime import datetime

import pytest

from core import dal
from core import domains
from core import models
from core.dal.tests.conftest import curr_0
from core.dal.tests.conftest import curr_10
from core.dal.tests.conftest import curr_failed
from core.dal.tests.conftest import curr_passed
from core.dal.tests.conftest import one_10
from core.dal.tests.conftest import one_20
from core.dal.tests.conftest import one_failed
from core.dal.tests.conftest import one_passed
from core.dal.tests.conftest import one_passed_failed
from core.dal.tests.conftest import prev_0
from core.dal.tests.conftest import prev_10
from core.dal.tests.conftest import prev_failed
from core.dal.tests.conftest import prev_passed
from infrastructure.tests.types import DBFactoryType
from utils.factory import FactoryMaker


class TestCreateOrUpdate:
    def test_not_exist(
        self,
        pass_log_repo: dal.PassLogDAL,
        user: models.User,
    ) -> None:
        assert not pass_log_repo.scalars()

        poll_create_or_update = pass_log_repo.update_or_create(
            content_type=domains.ContentTypeEnum.POLL,
            object_id=1,
            user_id=user.id,
        )
        poll_create_or_update(
            status=domains.PassStatusEnum.FAILED,
            earned_points=0,
        )

        assert pass_log_repo.scalars()

    def test_exist(self, pass_log_repo: dal.PassLogDAL, pass_log: models.PassLog) -> None:
        instance: models.PassLog = pass_log_repo.scalars()[0]
        assert instance
        initial_pk = instance.id

        poll_create_or_update = pass_log_repo.update_or_create(
            content_type=domains.ContentTypeEnum.POLL,
            object_id=1,
            user_id=pass_log.user.id,
        )
        poll_create_or_update(
            status=domains.PassStatusEnum.FAILED,
            earned_points=10,
        )

        instance = pass_log_repo.scalars()[0]
        assert instance
        assert instance.status is domains.PassStatusEnum.FAILED
        assert instance.earned_points == 10
        assert initial_pk == instance.id


class TestPollReport:
    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (None, (0, 0)),
            (one_passed, (1, 0)),
            (one_failed, (0, 1)),
            (one_passed_failed, (1, 1)),
        ],
    )
    def test_passed_failed(
        self,
        data: FactoryMaker | None,
        expected: tuple[int, int],
        pass_log_repo: dal.PassLogDAL,
        db_factory: DBFactoryType,
    ) -> None:
        db_factory(data)
        passed, failed = expected

        polls, _, _ = pass_log_repo.report(datetime.min, datetime.max)

        assert polls.passed == passed
        assert polls.failed == failed

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (None, 0),
            (one_10, 10),
            (one_10 & one_20, 30),
        ],
    )
    def test_summary(
        self,
        data: FactoryMaker | None,
        expected: int,
        pass_log_repo: dal.PassLogDAL,
        db_factory: DBFactoryType,
    ) -> None:
        db_factory(data)

        _, _, summary = pass_log_repo.report(datetime.min, datetime.max)

        assert summary.earned_points == expected


class TestMonthlyPollReport:
    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (None, (0, 0, 0, 0)),
            (curr_passed, (1, 1.0, 0, 0.0)),
            (curr_failed, (0, 0.0, 1, 1.0)),
            (curr_failed & curr_passed, (1, 1.0, 1, 1.0)),
            (prev_passed & curr_passed, (1, 0.0, 0, 0.0)),
            (prev_failed & curr_failed, (0, 0.0, 1, 0.0)),
            (prev_passed & prev_failed, (0, -1.0, 0, -1.0)),
            (prev_passed & prev_failed & curr_failed & curr_passed, (1, 0.0, 1, 0.0)),
        ],
    )
    def test_passed_failed(
        self,
        data: FactoryMaker | None,
        expected: tuple[int, float, int, float],
        pass_log_repo: dal.PassLogDAL,
        db_factory: DBFactoryType,
    ) -> None:
        db_factory(data)
        moment = datetime(2000, 1, 1)
        passed, passed_gain, failed, failed_gain = expected

        polls, _, _ = pass_log_repo.monthly_report(moment)

        assert polls.passed == passed
        assert polls.failed == failed
        assert polls.passed_gain == passed_gain
        assert polls.failed_gain == failed_gain

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (None, (0, 0.0)),
            (prev_0, (0, 0.0)),
            (prev_10, (0, -1.0)),
            (curr_0, (0, 0.0)),
            (curr_10, (10, 1.0)),
            (prev_0 & curr_10, (10, 1.0)),
            (prev_10 & curr_10, (10, 0.0)),
            (prev_10 & curr_0, (0, -1.0)),
        ],
    )
    def test_summary(
        self,
        data: FactoryMaker | None,
        expected: tuple[int, float],
        pass_log_repo: dal.PassLogDAL,
        db_factory: DBFactoryType,
    ) -> None:
        db_factory(data)
        moment = datetime(2000, 1, 1)
        earned_points, earned_points_gain = expected

        _, _, summary = pass_log_repo.monthly_report(moment)

        assert summary.earned_points == earned_points
        assert summary.earned_points_gain == earned_points_gain
