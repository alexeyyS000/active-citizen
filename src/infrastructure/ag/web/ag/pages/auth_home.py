from infrastructure.ag.web.ag.base import ag_app
from utils.rpa.web import BasePage


@ag_app.bind_page("/home")
class AuthHomePage(BasePage):
    pass
