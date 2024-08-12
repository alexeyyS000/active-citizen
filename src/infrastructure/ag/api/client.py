"""AG API client."""

from infrastructure.ag.api.schemas.novelty import NoveltiesSelectResponse
from infrastructure.ag.api.schemas.novelty import NoveltyGetResponse
from infrastructure.ag.api.schemas.points import PointsGetResponse
from infrastructure.ag.api.schemas.polls import PollGetResponse
from infrastructure.ag.api.schemas.polls import PollsSelectResponse
from utils.rpa.api import ApiClientBuilder

ag_api_client_builder = ApiClientBuilder("https://ag.mos.ru/api/service/")
ag_api_client_builder.add_endpoint("select_polls", "POST", "site/poll/select", PollsSelectResponse)
ag_api_client_builder.add_endpoint("get_poll", "POST", "site/poll/get", PollGetResponse)
ag_api_client_builder.add_endpoint("select_novelties", "POST", "site/novelty/select", NoveltiesSelectResponse)
ag_api_client_builder.add_endpoint("get_novelty", "POST", "site/novelty/get", NoveltyGetResponse)
ag_api_client_builder.add_endpoint("get_points", "POST", "site/poll/getPoints", PointsGetResponse)

AgApiClient = ag_api_client_builder.build("AgApiClient")
