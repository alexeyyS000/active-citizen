import secrets

from playwright.sync_api import Locator

from infrastructure.ag.web.ag.base import ag_app
from utils.rpa.web import BasePage
from utils.rpa.web import WebClient


@ag_app.bind_page("/polls")
class PollsPage(BasePage):
    pass


@ag_app.bind_page("/poll/{poll_id}")
class PollPage(BasePage):
    def __init__(self, web_client: WebClient):
        super().__init__(web_client)

        self.questions = self.page.locator("ag-poll-question")
        self.submit_btn = self.page.locator(".poll-page__submit-button")
        self._rnd = secrets.SystemRandom()

    def _pick_random_answer(self, answers: Locator) -> None:
        if answers.count() == 0:
            return

        answer_pos = self._rnd.randint(0, answers.count() - 1)
        answer = answers.nth(answer_pos)
        answer.click()

        answer_block = answer.locator("..")
        text_answer = answer_block.locator("textarea")
        is_text_answer = bool(text_answer.count())
        if is_text_answer:
            save_btn = answer_block.locator("text=Сохранить")
            message = "Хорошо"

            text_answer.fill(message)
            save_btn.click()

    def pass_(self):
        # read poll description...
        wait_timeout = 5 * 1000
        self.page.wait_for_timeout(wait_timeout)

        i = 0
        while True:
            passed = False
            question = self.questions.nth(i)
            exists_question = bool(question.count())
            if not exists_question:
                break

            # try answer on text variant
            text_answers = question.locator("ag-poll-variant .header-layout")
            if text_answers.count() != 0:
                self._pick_random_answer(text_answers)
                passed = True

            # try answer on variant
            answers = question.locator("ag-poll-variant label")
            if not passed and answers.count() != 0:
                self._pick_random_answer(answers)

            i += 1

        # wait before submit answers
        wait_timeout = 5 * 1000
        self.page.wait_for_timeout(wait_timeout)

        self.submit_btn.click()
