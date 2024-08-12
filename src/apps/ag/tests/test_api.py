"""
Testcases for AG API.
"""

import uuid

import pytest

from infrastructure.ag.api.schemas.novelty import NoveltiesFilterEnum
from infrastructure.ag.api.schemas.novelty import NoveltiesSelectRequest
from infrastructure.ag.api.schemas.novelty import NoveltyGetRequest
from infrastructure.ag.api.schemas.polls import PollGetRequest
from infrastructure.ag.api.schemas.polls import PollsFilterEnum
from infrastructure.ag.api.schemas.polls import PollsSelectRequest
from infrastructure.ag.web.client import AgWebClient


@pytest.mark.skip(reason="no way of currently testing this")
class TestApiAccess:
    def test_select_polls(self, ag_web_client: AgWebClient) -> None:
        params = {"request_id": str(uuid.uuid4())}
        request = PollsSelectRequest(
            count_per_page=100,
            filters=[PollsFilterEnum.AVAILABLE],
            categories=[],
            page_number=1,
        )

        try:
            response, _ = ag_web_client.api.select_polls(data=request, params=params)
            assert response.ok
        except Exception:
            pytest.fail("Cannot select polls")

    def test_get_poll(self, ag_web_client: AgWebClient) -> None:
        params = {"request_id": str(uuid.uuid4())}
        request = PollGetRequest(poll_id=100)

        try:
            response, _ = ag_web_client.api.get_poll(data=request, params=params)
            assert response.ok
        except Exception:
            pytest.fail("Cannot get poll")

    def test_select_novelties(self, ag_web_client: AgWebClient) -> None:
        params = {"request_id": str(uuid.uuid4())}
        request = NoveltiesSelectRequest(
            count_per_page=100,
            filter=[NoveltiesFilterEnum.ACTIVE],
            page_number=1,
        )

        try:
            response, _ = ag_web_client.api.select_novelties(data=request, params=params)
            assert response.ok
        except Exception:
            pytest.fail("Cannot select novelties")

    def test_get_novelty(self, ag_web_client: AgWebClient) -> None:
        params = {"request_id": str(uuid.uuid4())}
        request = NoveltyGetRequest(novelty_id=str(100))

        try:
            response, data = ag_web_client.api.get_novelty(data=request, params=params)
            assert response.ok
        except Exception:
            pytest.fail("Cannot get novelty")
