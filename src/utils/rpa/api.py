"""
RPA API utils.
"""

import typing
from urllib.parse import urljoin

from playwright.sync_api import APIRequestContext
from playwright.sync_api import APIResponse
from pydantic import BaseModel

ApiClientResponseType = tuple[APIResponse, BaseModel | dict[str, typing.Any]]


def _schema_to_dict(data: BaseModel | dict[str, typing.Any] | None) -> dict[str, typing.Any] | None:
    if isinstance(data, BaseModel):
        return data.model_dump()
    elif isinstance(data, dict):
        return data

    return None


class ApiClientBuilder:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._methods: dict[str, typing.Callable] = {}

    def _make_request(
        self,
        method: str,
        path: str,
        response_schema: type[BaseModel] | None,
    ):
        url = urljoin(self.base_url, path)

        def request(
            inner_self,
            data: BaseModel | dict[str, typing.Any] | None = None,
            form: BaseModel | dict[str, typing.Any] | None = None,
            params: dict | None = None,
            headers: dict | None = None,
            timeout: float | None = None,
        ) -> ApiClientResponseType:
            if not inner_self.api_req_context:
                raise RuntimeError("Client is not built")

            response = inner_self.api_req_context.fetch(
                url_or_request=url,
                method=method,
                params=params,
                headers=headers,
                data=_schema_to_dict(data),
                form=_schema_to_dict(form),
                timeout=timeout,
            )
            # TODO: handle response for forms
            # TODO: handle json parsing errors
            response_dict = response.json()
            if response_schema:
                parsed_response = response_schema.model_validate(response_dict)
                return response, parsed_response
            else:
                return response, response_dict

        return request

    def add_endpoint(
        self,
        name: str,
        method: str,
        path: str,
        response_schema: type[BaseModel] | None = None,
    ) -> "ApiClientBuilder":
        # TODO: add method name validation
        request = self._make_request(method, path, response_schema)
        self._methods[name] = request
        return self

    def build(self, cls_name: str) -> type:
        def constructor(inner_self, api_req_context: APIRequestContext):
            inner_self.api_req_context = api_req_context

        return type(cls_name, (object,), {**self._methods, "__init__": constructor})
