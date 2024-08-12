import secrets

from infrastructure.ag.web.ag.base import ag_app
from utils.rpa.web import BasePage
from utils.rpa.web import WebClient


@ag_app.bind_page("/novelties")
class NoveltiesPage(BasePage):
    pass


@ag_app.bind_page("/novelties/{novelty_id}")
class NoveltyPage(BasePage):
    def __init__(self, web_client: WebClient):
        super().__init__(web_client)
        self.rating = self.page.locator("button.information-grade__item")

    def pass_(self):
        # read novelty description...
        wait_timeout = 5 * 1000
        self.page.wait_for_timeout(wait_timeout)

        rating_pos = secrets.randbelow(self.rating.count())
        ball = self.rating.nth(rating_pos)
        ball.click()
