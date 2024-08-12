from core import models
from utils.permissions import BasePermission


class _IsAdmin(BasePermission):
    async def has_permission(self, **kwargs) -> bool:
        user: models.User = kwargs["user"]
        return user.admin


class _HasMosRuAccount(BasePermission):
    async def has_permission(self, **kwargs) -> bool:
        user: models.User = kwargs["user"]
        return bool(user.mos_ru_user_id)


class _IsApproved(BasePermission):
    async def has_permission(self, **kwargs) -> bool:
        user: models.User = kwargs["user"]
        return user.approved


IS_ADMIN = _IsAdmin()
IS_APPROVED = _IsApproved()
HAS_MOS_RU_ACCOUNT = _HasMosRuAccount()
