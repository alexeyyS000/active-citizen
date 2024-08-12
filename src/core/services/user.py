from core import models
from core.dal.user import AlertScheduleAsyncDAL
from core.dal.user import AlertScheduleDAL
from core.dal.user import UserAsyncDAL
from core.dal.user import UserDAL
from core.services.constants import DEFAULT_ALERT_TIME
from infrastructure.db.utils.enums import AlertScheduleTypeEnum


# TODO add transactions
# TODO made bulk_insert
class AsyncUserService:

    def __init__(self, user_dal: UserAsyncDAL, schedule_dal: AlertScheduleAsyncDAL):
        self._user_dal = user_dal
        self._schedule_dal = schedule_dal

    async def get_or_create(self, default: dict, **kwargs):
        user: models.User
        user, created = await self._user_dal.filter(**kwargs).load_related("mos_ru_user").get_or_create(**default)
        if created:
            await self._schedule_dal.filter(user_id=user.id, period=AlertScheduleTypeEnum.MONTHLY).create_one(
                user_id=user.id, period=AlertScheduleTypeEnum.MONTHLY, when=DEFAULT_ALERT_TIME
            )
            await self._schedule_dal.filter(user_id=user.id, period=AlertScheduleTypeEnum.DAILY).create_one(
                user_id=user.id, period=AlertScheduleTypeEnum.DAILY, when=DEFAULT_ALERT_TIME
            )
        return user, created


class UserService:

    def __init__(self, user_dal: UserDAL, schedule_dal: AlertScheduleDAL):
        self._user_dal = user_dal
        self._schedule_dal = schedule_dal

    def get_or_create(self, default: dict, **kwargs):
        user: models.User
        user, created = self._user_dal.filter(**kwargs).load_related("mos_ru_user").get_or_create(**default)
        if created:
            self._schedule_dal.filter(user_id=user.id, period=AlertScheduleTypeEnum.MONTHLY).create_one(
                user_id=user.id, period=AlertScheduleTypeEnum.MONTHLY, when=DEFAULT_ALERT_TIME
            )
            self._schedule_dal.filter(user_id=user.id, period=AlertScheduleTypeEnum.DAILY).create_one(
                user_id=user.id, period=AlertScheduleTypeEnum.DAILY, when=DEFAULT_ALERT_TIME
            )
        return user, created
