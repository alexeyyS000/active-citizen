"""
AG home pages.
"""

from infrastructure.ag.web.ag.base import ag_app
from infrastructure.ag.web.mos_ru.pages.login import LoginPage
from utils.rpa.web import BasePage
from utils.rpa.web import WebClient


@ag_app.bind_page("/home")
class HomePage(BasePage):
    def __init__(self, web_client: WebClient):
        super().__init__(web_client)
        self.login_btn = self.page.locator(".header__auth.reset-button")
        self.login_mos_ru_btn = self.page.locator("text=Войти через mos.ru")

    def goto_login(self) -> LoginPage:
        self.login_btn.click()
        self.login_mos_ru_btn.click()

        return LoginPage(self.web_client)
