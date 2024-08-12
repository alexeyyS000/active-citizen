from core import models
from infrastructure.db.utils.dal.async_ import SqlAlchemyAsyncRepository
from infrastructure.db.utils.dal.sync import SqlAlchemyRepository


class UserDAL(SqlAlchemyRepository):
    class Meta:
        model = models.User


class UserAsyncDAL(SqlAlchemyAsyncRepository):
    class Meta:
        model = models.User


class AlertScheduleDAL(SqlAlchemyRepository):
    class Meta:
        model = models.AlertSchedule


class AlertScheduleAsyncDAL(SqlAlchemyAsyncRepository):
    class Meta:
        model = models.AlertSchedule


class TaskLogDAL(SqlAlchemyRepository):
    class Meta:
        model = models.TaskLog


class TaskLogAsyncDAL(SqlAlchemyAsyncRepository):
    class Meta:
        model = models.TaskLog


class MosRuUserDAL(SqlAlchemyRepository):
    class Meta:
        model = models.MosRuUser


class MosRuUserAsyncDAL(SqlAlchemyAsyncRepository):
    class Meta:
        model = models.MosRuUser
