import uuid
from datetime import datetime
from http import HTTPStatus

import structlog
from celery import shared_task
from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject

from core import dal
from core import domains
from infrastructure.ag.api.schemas.novelty import NoveltiesFilterEnum
from infrastructure.ag.api.schemas.novelty import NoveltyGetRequest
from infrastructure.ag.api.schemas.novelty import NoveltyStatusEnum
from infrastructure.ag.api.schemas.polls import PollGetRequest
from infrastructure.ag.api.schemas.polls import PollKindEnum
from infrastructure.ag.api.schemas.polls import PollsFilterEnum
from infrastructure.ag.api.schemas.polls import PollStatusEnum
from infrastructure.ag.web.ag.pages.novelties import NoveltyPage
from infrastructure.ag.web.ag.pages.polls import PollPage
from infrastructure.ag.web.client import AgWebClient
from infrastructure.config import DEFAULT_TIMEZONE
from infrastructure.worker.container import WorkerContainer
from utils.pagination import PageSizePagination

logger = structlog.get_logger()


@shared_task(
    name="tasks.pass_polls",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
@inject
def pass_polls(
    tg_id: int,
    user_dal: dal.UserDAL = Provide[WorkerContainer.user_dal],
    mos_ru_user_dal: dal.MosRuUserDAL = Provide[WorkerContainer.mos_ru_user_dal],
    ag_web_client: AgWebClient = Provide[WorkerContainer.ag_web_client],
):
    log = logger.bind(tg_id=tg_id)

    user = user_dal.filter(tg_id=tg_id).load_related("mos_ru_user").first()
    if user is None:
        log.error("Cannot pass polls because couldn't find user.")
        return

    if user.mos_ru_user is None:
        log.warning("Cannot pass polls because user doesn't have mos.ru credentials.")
        return

    mos_ru_user = user.mos_ru_user

    if mos_ru_user.browser_state:
        ag_web_client.state_from_dict(mos_ru_user.browser_state)

    with ag_web_client as client:
        try:
            client.login(mos_ru_user.login, mos_ru_user.password)
        except client.Error.MosRuAuthorizationError as err:
            # TODO: create alerting for unsuccessful authorization
            log.error("Unsuccessful sign in attempt")
            raise err

        state = ag_web_client.read_state()
        mos_ru_user_dal.filter(id=mos_ru_user.id).update(browser_state=state)

        # pass available polls
        for poll in client.iter_polls(filters=[PollsFilterEnum.AVAILABLE]):
            pass_poll.delay(
                tg_id=tg_id,
                poll_id=poll.id,
            )


@shared_task(
    name="tasks.pass_novelties",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
@inject
def pass_novelties(
    tg_id: int,
    user_dal: dal.UserDAL = Provide[WorkerContainer.user_dal],
    mos_ru_user_dal: dal.MosRuUserDAL = Provide[WorkerContainer.mos_ru_user_dal],
    ag_web_client: AgWebClient = Provide[WorkerContainer.ag_web_client],
):
    log = logger.bind(tg_id=tg_id)

    user = user_dal.filter(tg_id__exact=tg_id).load_related("mos_ru_user").first()
    if user is None:
        log.error("Cannot pass novelties because couldn't find user.")
        return

    if user.mos_ru_user is None:
        log.warning("Cannot pass novelties because user doesn't have mos.ru credentials.")
        return

    mos_ru_user = user.mos_ru_user

    if mos_ru_user.browser_state:
        ag_web_client.state_from_dict(mos_ru_user.browser_state)

    with ag_web_client as client:
        try:
            client.login(mos_ru_user.login, mos_ru_user.password)
        except client.Error.MosRuAuthorizationError as err:
            log.error("Unsuccessful sign in attempt")
            raise err

        state = ag_web_client.read_state()
        mos_ru_user_dal.filter(id=mos_ru_user.id).update(browser_state=state)

        for novelty in client.iter_novelties(filters=[NoveltiesFilterEnum.ACTIVE]):
            pass_novelty.delay(
                tg_id=tg_id,
                novelty_id=novelty.id,
            )


@shared_task(
    name="tasks.pass_poll",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
@inject
def pass_poll(
    tg_id: int,
    poll_id: int,
    user_dal: dal.UserDAL = Provide[WorkerContainer.user_dal],
    mos_ru_user_dal: dal.MosRuUserDAL = Provide[WorkerContainer.mos_ru_user_dal],
    pass_log_repo: dal.PassLogDAL = Provide[WorkerContainer.pass_log_dal],
    ag_web_client: AgWebClient = Provide[WorkerContainer.ag_web_client],
):
    log = logger.bind(poll_id=poll_id, tg_id=tg_id)

    user = user_dal.filter(tg_id__exact=tg_id).load_related("mos_ru_user").first()
    if user is None:
        log.error("Cannot pass poll because couldn't find user.")
        return

    if user.mos_ru_user is None:
        log.warning("Cannot pass poll because user doesn't have mos.ru credentials.")
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
        request = PollGetRequest(poll_id=poll_id)
        response, data = client.api.get_poll(data=request, params=params)

        if not data.result or response.status is HTTPStatus.NOT_FOUND:
            log.warning("Poll not found.")
            return

        poll_kind = PollKindEnum(data.result.details.kind)
        if poll_kind is PollKindEnum.GROUP:
            log.warning("Cannot handle group polls.")
            return

        poll = data.result.details
        if poll.status is PollStatusEnum.PASSED:
            log.info("Poll already passed.")
            return

        now = datetime.now(DEFAULT_TIMEZONE)
        poll_create_or_update = pass_log_repo.update_or_create(
            content_type=domains.ContentTypeEnum.POLL,
            object_id=poll_id,
            user_id=user.id,
        )

        try:
            client.pass_polls(poll_id)
        except PollPage.PageNotFoundError:
            log.warning("Poll was not found")
            return
        except Exception as exc:
            log.error("Cannot pass current poll. Something wrong.")
            log.exception(exc)

            poll_create_or_update(
                status=domains.PassStatusEnum.FAILED,
                earned_points=0,
                created_at=now,
                updated_at=now,
            )

            raise exc

        log.info("Poll successfully complete.")

        poll_create_or_update(
            status=domains.PassStatusEnum.PASSED,
            earned_points=data.result.details.points,
            created_at=now,
            updated_at=now,
        )


@shared_task(
    name="tasks.pass_novelty",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
@inject
def pass_novelty(
    tg_id: int,
    novelty_id: int,
    user_dal: dal.UserDAL = Provide[WorkerContainer.user_dal],
    mos_ru_user_dal: dal.MosRuUserDAL = Provide[WorkerContainer.mos_ru_user_dal],
    pass_log_repo: dal.PassLogDAL = Provide[WorkerContainer.pass_log_dal],
    ag_web_client: AgWebClient = Provide[WorkerContainer.ag_web_client],
):
    log = logger.bind(novelty_id=novelty_id, tg_id=tg_id)

    user = user_dal.filter(tg_id__exact=tg_id).load_related("mos_ru_user").first()
    if user is None:
        log.error("Cannot pass novelty because couldn't find user.")
        return

    if user.mos_ru_user is None:
        log.warning("Cannot pass novelty because user doesn't have mos.ru credentials.")
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
        request = NoveltyGetRequest(novelty_id=str(novelty_id))
        response, data = client.api.get_novelty(data=request, params=params)

        if not data.result or response.status is HTTPStatus.NOT_FOUND:
            log.warning("Novelty not found")
            return

        novelty = data.result.details
        if novelty.status is NoveltyStatusEnum.PASSED:
            log.warning("Novelty already passed")
            return

        now = datetime.now(DEFAULT_TIMEZONE)
        novelty_create_or_update = pass_log_repo.update_or_create(
            content_type=domains.ContentTypeEnum.NOVELTY,
            object_id=novelty_id,
            user_id=user.id,
        )

        try:
            client.pass_novelties(novelty_id)
        except NoveltyPage.PageNotFoundError:
            log.warning("Novelty not found")
            return
        except Exception as exc:
            log.error("Cannot pass current novelty. Something wrong.")
            log.exception(exc)

            novelty_create_or_update(
                status=domains.PassStatusEnum.FAILED,
                earned_points=0,
                created_at=now,
                updated_at=now,
            )

            raise exc

        log.info("Novelty successfully complete.")

        novelty_create_or_update(
            status=domains.PassStatusEnum.PASSED,
            earned_points=data.result.details.points,
            created_at=now,
            updated_at=now,
        )


@shared_task(
    name="tasks.periodic_pass_novelties",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
@inject
def periodic_pass_novelties(
    user_dal: dal.UserDAL = Provide[WorkerContainer.user_dal],
) -> None:
    pagination = PageSizePagination(page_size=100)
    cursor = user_dal.filter(mos_ru_user_id__isnull=False).order_by(tg_id=True).paginate(pagination)

    # TODO: handle retry
    for _, users in cursor:
        for user in users:
            pass_novelties.delay(tg_id=user.tg_id)


@shared_task(
    name="tasks.periodic_pass_polls",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
@inject
def periodic_pass_polls(
    user_dal: dal.UserDAL = Provide[WorkerContainer.user_dal],
) -> None:
    pagination = PageSizePagination(page_size=100)
    cursor = user_dal.filter(mos_ru_user_id__isnull=False).order_by(tg_id=True).paginate(pagination)

    # TODO: handle retry
    for _, users in cursor:
        for user in users:
            pass_polls.delay(tg_id=user.tg_id)
