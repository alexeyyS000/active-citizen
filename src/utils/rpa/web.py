import contextlib
import json
import typing
from http import HTTPStatus
from os import path
from pathlib import Path
from typing import Type
from urllib.parse import urljoin

from playwright.sync_api import Page
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

from infrastructure.minio.client import BaseBucketClient
from utils.dt import get_utc_now
from utils.rpa.exceptions import _PageNotFoundError


class BasePage:
    url: str = ""

    PageNotFoundError = _PageNotFoundError

    def __init__(self, web_client: "WebClient"):
        self.web_client = web_client
        self.page: Page = web_client.page


class WebApp:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def bind_page(self, path: str):
        def wrap(cls: Type[BasePage]):
            cls.url = urljoin(self.base_url, path)
            return cls

        return wrap


class WebClient(contextlib.AbstractContextManager):
    class Error:
        """
        Web client error accessor. It's used for exception aggregation.
        """

        pass

    class Config:
        """
        Web client configuration.
        """

        # TODO: add typing
        api_client_factory: type

    def __init__(
        self,
        state_path: Path | None = None,
        headless: bool = False,
        files_client: BaseBucketClient | None = None,
        tmp_trace_log_dir: Path | None = None,
    ):
        now = get_utc_now()
        default_state_path = Path("/tmp") / f"state_{now!s}.json"  # noqa: S108
        self._state_path = state_path or default_state_path
        self._headless = headless
        self._files_client = files_client
        self._api_client = None
        default_trace_log_dir = Path("/tmp") / "trace_logs"  # noqa: S108
        self._tmp_trace_log_dir = tmp_trace_log_dir or default_trace_log_dir

    def _init_api_client(self):
        if self.Config.api_client_factory:
            api_context = self.page.context.request
            self._api_client = self.Config.api_client_factory(api_context)

    def state_from_dict(self, new_state: dict) -> None:
        with open(self._state_path, "w") as file:
            content = json.dumps(new_state)
            file.write(content)

    @property
    def api(self):
        return self._api_client

    @classmethod
    def _format_url(cls, url: str, path_params: dict[str, typing.Any]) -> str:
        for path_param, value in path_params.items():
            url = url.replace("{" + path_param + "}", str(value))
        return url

    def goto(self, web_page: Type[BasePage], **kwargs):
        url = self._format_url(web_page.url, kwargs)
        response = self.page.goto(url)

        if response is None:
            return web_page(self)

        if response.status is HTTPStatus.NOT_FOUND:
            raise web_page.PageNotFoundError

        return web_page(self)

    def start_recording(self):
        if not self._files_client:
            return

        if not self.context:
            return

        self.context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True,
        )

    def stop_recording(self):
        if not self._files_client:
            return

        if not self.context:
            return

        now = get_utc_now()

        filename = f"trace_{now!s}.zip"
        output_path = str(self._tmp_trace_log_dir / filename)

        self.context.tracing.stop(path=output_path)

        content_type = "application/zip"
        self._files_client.upload_file(filename, output_path, content_type)

    def __enter__(self):
        self._playwright_context = sync_playwright()
        self.playwright = self._playwright_context.start()

        self.browser = self.playwright.chromium.launch(
            headless=self._headless,
            slow_mo=1000,
        )

        if self._state_path and path.exists(self._state_path):
            self.context = self.browser.new_context(storage_state=self._state_path)
            self.page = self.context.new_page()
        else:
            self.page = self.browser.new_page()
            self.context = self.page.context

        stealth_sync(self.page)

        self._init_api_client()

        self.start_recording()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_recording()
        self.close()
        self._playwright_context.__exit__()

    def read_state(self) -> dict:
        with open(self._state_path, "r") as file:
            return json.load(file)

    def save_state(self):
        if self._state_path:
            self.page.context.storage_state(path=self._state_path)

    def close(self) -> None:
        """
        Close web client.
        """
        self.save_state()
        self.browser.close()
