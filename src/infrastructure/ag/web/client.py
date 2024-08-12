"""
AG client.
"""

import itertools
import typing
import uuid
from pathlib import Path

from infrastructure.ag.api.client import AgApiClient
from infrastructure.ag.api.schemas.novelty import NoveltiesFilterEnum
from infrastructure.ag.api.schemas.novelty import NoveltiesSelectRequest
from infrastructure.ag.api.schemas.novelty import Novelty
from infrastructure.ag.api.schemas.polls import Poll
from infrastructure.ag.api.schemas.polls import PollKindEnum
from infrastructure.ag.api.schemas.polls import PollsFilterEnum
from infrastructure.ag.api.schemas.polls import PollsSelectRequest
from infrastructure.ag.web.ag.exceptions import _ForbiddenDueUnauthorizedError
from infrastructure.ag.web.ag.pages.auth_home import AuthHomePage
from infrastructure.ag.web.ag.pages.home import HomePage
from infrastructure.ag.web.ag.pages.novelties import NoveltyPage
from infrastructure.ag.web.ag.pages.polls import PollPage
from infrastructure.ag.web.mos_ru.exception import _MosRuAuthorizationError
from infrastructure.minio.client import BaseBucketClient
from utils.rpa.web import WebClient


class AgWebClient(WebClient):
    class Error(WebClient.Error):
        MosRuAuthorizationError = _MosRuAuthorizationError
        ForbiddenDueUnauthorizedError = _ForbiddenDueUnauthorizedError

    class Config:
        # TODO: add typing
        api_client_factory = AgApiClient

    def __init__(
        self,
        state_path: Path | None = None,
        headless: bool = False,
        files_client: BaseBucketClient | None = None,
        tmp_trace_log_dir: Path | None = None,
    ):
        super().__init__(state_path, headless, files_client, tmp_trace_log_dir)

    def is_authorized(self) -> bool:
        return self.page.locator(".user-profile").count() > 0

    def login(self, login: str, password: str) -> AuthHomePage:
        home_page = self.goto(HomePage)

        if self.is_authorized():
            return AuthHomePage(self)

        mos_ru_login_page = home_page.goto_login()

        auth_home_page = mos_ru_login_page.login(login, password)

        self.save_state()

        return auth_home_page

    def pass_polls(self, poll_id: int):
        poll_page = self.goto(PollPage, poll_id=poll_id)
        poll_page.pass_()

    def pass_novelties(self, novelty_id: int):
        novelty_page = self.goto(NoveltyPage, novelty_id=novelty_id)
        novelty_page.pass_()

    def iter_polls(
        self,
        filters: list[PollsFilterEnum] | None = None,
        categories: list[int] | None = None,
        count_per_page: int = 100,
        page_number: int = 1,
    ) -> typing.Iterable[Poll]:
        if not filters:
            filters = []

        if not categories:
            categories = []

        params = {"request_id": str(uuid.uuid4())}
        request = PollsSelectRequest(
            count_per_page=count_per_page,
            filters=filters,
            categories=categories,
            page_number=page_number,
        )
        _, data = self.api.select_polls(data=request, params=params)
        if not data.result:
            raise self.Error.ForbiddenDueUnauthorizedError

        polls = data.result.polls
        group_polls = filter(lambda p: p.kind is PollKindEnum.GROUP, polls)

        children_polls = []
        for group_poll in group_polls:
            request.parent_id = group_poll.id
            _, data = self.api.select_polls(data=request, params=params)

            if not data.result:
                continue

            children_polls.extend(data.result.polls)

        polls_without_groups = filter(
            lambda p: p.kind is not PollKindEnum.GROUP,
            polls,
        )

        yield from itertools.chain(polls_without_groups, children_polls)

    def iter_novelties(
        self,
        filters: list[NoveltiesFilterEnum] | None = None,
        count_per_page: int = 100,
        page_number: int = 1,
    ) -> typing.Iterable[Novelty]:
        if not filters:
            filters = []

        params = {"request_id": str(uuid.uuid4())}
        request = NoveltiesSelectRequest(
            count_per_page=count_per_page,
            filter=filters,
            page_number=page_number,
        )
        _, data = self.api.select_novelties(data=request, params=params)
        if not data.result:
            raise self.Error.ForbiddenDueUnauthorizedError

        yield from data.result.novelties
