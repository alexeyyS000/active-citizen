from datetime import datetime
from uuid import UUID

import sqlalchemy as sa

from core import domains
from core import models
from infrastructure.db.utils.dal.sync import SqlAlchemyRepository
from infrastructure.db.utils.shortcuts.math import gain_stmt
from infrastructure.db.utils.shortcuts.math import interval_filter
from utils.dt import day_interval
from utils.dt import month_interval


class PassLogDAL(SqlAlchemyRepository):
    class Meta:
        model = models.PassLog

    @staticmethod
    def summary_statistic_stmt() -> sa.Select:
        earned_points = sa.func.coalesce(sa.func.sum(models.PassLog.earned_points), 0).label("earned_points")
        return sa.select(earned_points).filter_by(status=domains.PassStatusEnum.PASSED)

    @staticmethod
    def amount_statistic_stmt(content_type: domains.ContentTypeEnum) -> sa.Select:
        passed = sa.case(
            ((models.PassLog.status == domains.PassStatusEnum.PASSED), 1),
            else_=0,
        )
        failed = sa.case(
            ((models.PassLog.status == domains.PassStatusEnum.FAILED), 1),
            else_=0,
        )
        amount_passed = sa.func.coalesce(sa.func.sum(passed), 0).label("passed")
        amount_failed = sa.func.coalesce(sa.func.sum(failed), 0).label("failed")
        return sa.select(amount_passed, amount_failed).filter_by(content_type=content_type)

    def daily_report(self, today: datetime, user_id: UUID | None = None):
        # TODO: implement dt_interval
        begin, end = day_interval(today)
        return self.report(begin, end, user_id)

    def report(self, from_: datetime, to: datetime, user_id: UUID | None = None):
        with self.session_factory() as session:
            curr_filter = interval_filter(models.PassLog.created_at, from_, to)
            polls_stmt = self.amount_statistic_stmt(domains.ContentTypeEnum.POLL).filter(curr_filter)

            if user_id is not None:
                polls_stmt = polls_stmt.filter_by(user_id=user_id)

            res = session.execute(polls_stmt)
            polls = res.first()

            novelties_stmt = self.amount_statistic_stmt(domains.ContentTypeEnum.NOVELTY).filter(curr_filter)
            if user_id is not None:
                novelties_stmt = novelties_stmt.filter_by(user_id=user_id)

            res = session.execute(novelties_stmt)
            novelties = res.first()

            summary_stmt = self.summary_statistic_stmt().filter(curr_filter)
            if user_id is not None:
                summary_stmt = summary_stmt.filter_by(user_id=user_id)

            res = session.execute(summary_stmt)
            summary = res.first()

            return polls, novelties, summary

    def monthly_report(self, today: datetime, user_id: UUID | None = None):
        # TODO: implement dt_interval
        interval = month_interval(today)
        with self.session_factory() as session:
            polls_stmt = gain_stmt(
                self.amount_statistic_stmt(domains.ContentTypeEnum.POLL),
                models.PassLog.created_at,
                *interval,
                ["passed", "failed"],
            )
            if user_id is not None:
                polls_stmt = polls_stmt.filter_by(user_id=user_id)

            res = session.execute(polls_stmt)
            polls = res.first()

            novelties_stmt = gain_stmt(
                self.amount_statistic_stmt(domains.ContentTypeEnum.NOVELTY),
                models.PassLog.created_at,
                *interval,
                ["passed", "failed"],
            )
            if user_id is not None:
                novelties_stmt = novelties_stmt.filter_by(user_id=user_id)

            res = session.execute(novelties_stmt)
            novelties = res.first()

            summary_stmt = gain_stmt(
                self.summary_statistic_stmt(),
                models.PassLog.created_at,
                *interval,
                ["earned_points"],
            )
            if user_id is not None:
                summary_stmt = summary_stmt.filter_by(user_id=user_id)

            res = session.execute(summary_stmt)
            summary = res.first()

            return polls, novelties, summary
