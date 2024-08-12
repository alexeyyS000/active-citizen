from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from infrastructure.ag.web.ag.pages.auth_home import AuthHomePage
from infrastructure.ag.web.mos_ru.exception import _MosRuAuthorizationError
from utils.rpa.web import BasePage
from utils.rpa.web import WebClient


class LoginPage(BasePage):
    def __init__(self, web_client: WebClient):
        super().__init__(web_client)

        self._login_locate_timeout = 15000
        self.login_field = self.page.locator('[name="login"]')
        self.password_field = self.page.locator('[name="password"]')
        self.submit_btn = self.page.locator("#bind")
        self.error_msg = self.page.locator("#gErrs")

    def _login(self, login: str, password: str) -> None:
        if "ag.mos.ru" in self.page.url:
            # if the URL did not change, it means user successfully logged in without a credential check
            return

        try:
            self.login_field.fill(login, timeout=self._login_locate_timeout)
        except PlaywrightTimeoutError:
            # ignore if login field is prefilled
            pass

        self.password_field.fill(password)
        self.submit_btn.click()

    def login(self, login: str, password: str):
        self._login(login, password)

        if "login.mos.ru" in self.page.url:
            msg = self.error_msg.text_content()
            if msg:
                raise _MosRuAuthorizationError(msg.strip())

        return AuthHomePage(self.web_client)
