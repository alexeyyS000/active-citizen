"""
Testcases for AG web.
"""

import pytest
from playwright.sync_api import expect

from core import models
from infrastructure.ag.web.client import AgWebClient


@pytest.mark.skip(reason="no way of currently testing this")
def test_login(ag_web_client: AgWebClient, mos_ru_user: models.MosRuUser) -> None:
    ag_web_client.login(mos_ru_user.login, mos_ru_user.password)

    profile_el = ag_web_client.page.locator("ag-profile-info")
    expect(profile_el).to_be_attached()
