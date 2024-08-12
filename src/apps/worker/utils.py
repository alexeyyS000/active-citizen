from celery.result import AsyncResult

STATUSES = ["PENDING", "RECEIVED", "STARTED"]


def task_revoke(task_id: str, terminate: bool = False):

    existing_task = AsyncResult(task_id)

    if existing_task.status in STATUSES:
        existing_task.revoke(terminate=terminate)
        return True
    else:
        return False
