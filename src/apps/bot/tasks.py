import uuid
from datetime import datetime
from datetime import time
from datetime import timedelta
from datetime import timezone

import pytz
import structlog
from celery import shared_task
from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject

from apps.worker.utils import task_revoke
from core import dal
from core.dal import PassLogDAL
from infrastructure.ag.api.schemas.novelty import NoveltiesFilterEnum
from infrastructure.ag.api.schemas.novelty import NoveltiesSelectRequest
from infrastructure.ag.api.schemas.polls import PollsFilterEnum
from infrastructure.ag.api.schemas.polls import PollsSelectRequest
from infrastructure.ag.web.client import AgWebClient
from infrastructure.bot.client.sync import TelegramBotClient
from infrastructure.bot.templates import TelegramTemplate
from infrastructure.bot.templates import render_error
from infrastructure.config import DEFAULT_TIMEZONE_NAME
from infrastructure.db.utils.enums import AlertScheduleTypeEnum
from infrastructure.worker.container import WorkerContainer
from utils.dt import month_interval
from utils.pagination import PageSizePagination

logger = structlog.get_logger()


@shared_task(
    name="tasks.send_daily_report",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
@inject
def send_daily_report(
    tg_id: int,
    telegram_bot_client: TelegramBotClient = Provide[WorkerContainer.telegram_bot_client],
    pass_log_dal: dal.PassLogDAL = Provide[WorkerContainer.pass_log_dal],
    user_dal: dal.UserDAL = Provide[WorkerContainer.user_dal],
    mos_ru_user_dal: dal.MosRuUserDAL = Provide[WorkerContainer.mos_ru_user_dal],
    ag_web_client: AgWebClient = Provide[WorkerContainer.ag_web_client],
    telegram_template: TelegramTemplate = Provide[WorkerContainer.telegram_template],
    schedule_dal: dal.AlertScheduleAsyncDAL = Provide[WorkerContainer.schedule_sync_dal],
    task_log_dal: dal.TaskLogDAL = Provide[WorkerContainer.task_log_sync_dal],
):
    log = logger.bind(tg_id=tg_id)

    user = user_dal.filter(tg_id__exact=tg_id).load_related("mos_ru_user").first()
    if user is None:
        message = "Cannot send daily report because couldn't find user."

        response = render_error(message)
        telegram_bot_client.send_response(tg_id, response)

        log.error(message)

        return

    if user.mos_ru_user is None:
        message = "Cannot send daily report because user doesn't have mos.ru credentials."

        response = render_error(message)
        telegram_bot_client.send_response(tg_id, response)

        log.error(message)

        return

    mos_ru_user = user.mos_ru_user

    if mos_ru_user.browser_state:
        ag_web_client.state_from_dict(mos_ru_user.browser_state)

    with ag_web_client as client:
        try:
            client.login(mos_ru_user.login, mos_ru_user.password)
        except client.Error.MosRuAuthorizationError as err:
            log.error("Unsuccessful sign in attempt.")
            raise err

        state = ag_web_client.read_state()
        mos_ru_user_dal.filter(id=mos_ru_user.id).update(browser_state=state)

        params = {"request_id": str(uuid.uuid4())}
        request_novelties = NoveltiesSelectRequest(
            count_per_page=100,
            filter=[NoveltiesFilterEnum.ACTIVE],
            page_number=1,
        )
        _, novelties_data = client.api.select_novelties(data=request_novelties, params=params)

        params = {"request_id": str(uuid.uuid4())}
        request_polls = PollsSelectRequest(
            count_per_page=100,
            filters=[PollsFilterEnum.AVAILABLE],
            categories=[],
            page_number=1,
        )
        _, polls_data = client.api.select_polls(data=request_polls, params=params)

    if not novelties_data.result or not polls_data.result:
        log.error("Something went wrong: can not get data.")
        raise Exception

    today = datetime.utcnow()
    polls, novelties, summary = pass_log_dal.daily_report(today, user.id)
    available_novelties = len(novelties_data.result.novelties)
    available_polls = len(polls_data.result.polls)
    status = novelties_data.result.status
    current_balance = None if not status else status.current_points

    # the current balance is none for not authorized users
    if current_balance is None:
        message = render_error("Cannot send daily report because couldn't log in.")
        telegram_bot_client.send_response(tg_id, message)

        log.error("Daily report wasn't sent because couldn't log in.")

        return

    message = telegram_template.render(
        "report/daily.html",
        user.language_code,
        today=today,
        available_polls=available_polls,
        available_novelties=available_novelties,
        novelties=novelties,
        polls=polls,
        summary=summary,
        current_balance=current_balance,
    )
    telegram_bot_client.send_response(tg_id, message)

    schedule = schedule_dal.filter(user_id=user.id, period=AlertScheduleTypeEnum.DAILY)
    task_log_dal.filter(id=schedule.first().task_log_id).update(deleted_at=datetime.now(timezone.utc))
    schedule.update(task_log_id=None)

    log.info("Daily report was sent.")


@shared_task(
    name="tasks.send_monthly_report",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
@inject
def send_monthly_report(
    tg_id: int,
    user_dal: dal.UserDAL = Provide[WorkerContainer.user_dal],
    pass_log_repo: PassLogDAL = Provide[WorkerContainer.pass_log_dal],
    telegram_bot_client: TelegramBotClient = Provide[WorkerContainer.telegram_bot_client],
    telegram_template: TelegramTemplate = Provide[WorkerContainer.telegram_template],
    schedule_dal: dal.AlertScheduleAsyncDAL = Provide[WorkerContainer.schedule_sync_dal],
    task_log_dal: dal.TaskLogDAL = Provide[WorkerContainer.task_log_sync_dal],
):
    log = logger.bind(tg_id=tg_id)

    user = user_dal.filter(tg_id__exact=tg_id).first()
    if user is None:
        message = "Cannot send monthly report because couldn't find user."

        response = render_error(message)
        telegram_bot_client.send_response(tg_id, response)

        log.error(message)

        return

    today = datetime.utcnow()
    begin_month = today.replace(day=1)
    last_month = begin_month - timedelta(days=1)
    first_day, last_day = month_interval(last_month)
    polls, novelties, summary = pass_log_repo.monthly_report(today, user.id)

    message = telegram_template.render(
        "report/monthly.html",
        user.language_code,
        begin=first_day,
        end=last_day,
        novelties=novelties,
        polls=polls,
        summary=summary,
    )
    telegram_bot_client.send_response(tg_id, message)

    schedule = schedule_dal.filter(user_id=user.id, period=AlertScheduleTypeEnum.MONTHLY)
    task_log_dal.filter(id=schedule.first().task_log_id).update(deleted_at=datetime.now(timezone.utc))
    schedule.update(task_log_id=None)

    log.info("Monthly report was sent.")


@shared_task(
    name="tasks.send_daily_reports",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
@inject
def send_daily_reports(
    user_dal: dal.UserDAL = Provide[WorkerContainer.user_dal],
    schedule_dal: dal.AlertScheduleDAL = Provide[WorkerContainer.schedule_sync_dal],
    task_log_dal: dal.TaskLogDAL = Provide[WorkerContainer.task_log_sync_dal],
) -> None:

    pagination = PageSizePagination(page_size=100)
    cursor = user_dal.filter(mos_ru_user_id__isnull=False).order_by(tg_id=True).paginate(pagination)

    for _, users in cursor:
        for user in users:

            time = schedule_dal.filter(user_id=user.id, period=AlertScheduleTypeEnum.DAILY)

            task_log = task_log_dal.create_one()

            default_tz = pytz.timezone(DEFAULT_TIMEZONE_NAME)
            now = datetime.now(default_tz)
            eta_time = datetime.combine(now.date(), time.first().when).astimezone(default_tz)

            send_daily_report.apply_async(args=(user.tg_id,), task_id=str(task_log.id), eta=eta_time)
            time.update(task_log_id=task_log.id)


@shared_task(
    name="tasks.send_monthly_reports",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
@inject
def send_monthly_reports(
    user_dal: dal.UserDAL = Provide[WorkerContainer.user_dal],
    schedule_dal: dal.AlertScheduleAsyncDAL = Provide[WorkerContainer.schedule_sync_dal],
    task_log_dal: dal.TaskLogDAL = Provide[WorkerContainer.task_log_sync_dal],
) -> None:

    pagination = PageSizePagination(page_size=100)
    cursor = user_dal.filter(mos_ru_user_id__isnull=False).order_by(tg_id=True).paginate(pagination)

    for _, users in cursor:
        for user in users:

            time = schedule_dal.filter(user_id=user.id, period=AlertScheduleTypeEnum.MONTHLY)

            task_log = task_log_dal.create_one()

            default_tz = pytz.timezone(DEFAULT_TIMEZONE_NAME)
            now = datetime.now(default_tz)
            eta_time = datetime.combine(now.date(), time.first().when).astimezone(default_tz)

            send_monthly_report.apply_async(args=(user.tg_id,), task_id=str(task_log.id), eta=eta_time)
            time.update(task_log_id=task_log.id)


@shared_task(
    name="tasks.redefine_alert_task",
)
@inject
def redefine_alert_task(
    task_id: str,
    new_time: time,
    tg_id,
    schedule_type: AlertScheduleTypeEnum,
    schedule_dal: dal.AlertScheduleDAL = Provide[WorkerContainer.schedule_sync_dal],
    task_log_dal: dal.TaskLogDAL = Provide[WorkerContainer.task_log_sync_dal],
):

    is_revoked = task_revoke(task_id)

    if is_revoked:

        default_tz = pytz.timezone(DEFAULT_TIMEZONE_NAME)
        now = datetime.now(default_tz)
        eta = datetime.combine(now.date(), new_time).astimezone(default_tz)

        task_log_dal.filter(id=task_id).update(deleted_at=datetime.now(timezone.utc))
        task_log = task_log_dal.create_one()
        schedule_dal.filter(task_log_id=task_id).update(task_log_id=task_log.id)

        if schedule_type == AlertScheduleTypeEnum.DAILY:
            send_daily_report.apply_async(args=(tg_id,), task_id=str(task_log.id), eta=eta)
        if schedule_type == AlertScheduleTypeEnum.MONTHLY:
            send_monthly_report.apply_async(args=(tg_id,), task_id=str(task_log.id), eta=eta)
