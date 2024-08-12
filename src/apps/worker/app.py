"""
Celery application.
"""

import structlog
from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging
from celery.signals import task_prerun

from infrastructure.config import DEFAULT_TIMEZONE_NAME
from infrastructure.logger.utils import setup_loki_config
from infrastructure.worker.config import WorkerSettings
from infrastructure.worker.container import WorkerContainer
from utils.logger import setup_logger

settings = WorkerSettings()
celery = Celery(
    "tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    broker_connection_retry_on_startup=True,
)

celery.autodiscover_tasks(["apps.ag", "apps.bot"])

celery.conf.beat_schedule = {
    "pass-novelties-every-day": {
        "task": "tasks.periodic_pass_novelties",
        "schedule": crontab(hour="9,19", minute="0"),
    },
    "pass-polls-every-day": {
        "task": "tasks.periodic_pass_polls",
        "schedule": crontab(hour="9,19", minute="0"),
    },
    "send-daily-reports": {
        "task": "tasks.send_daily_reports",
        "schedule": crontab(hour="18", minute="19"),
    },
    "send-monthly-reports": {
        "task": "tasks.send_monthly_reports",
        "schedule": crontab(hour="0", minute="0", day_of_month="1", month_of_year="*"),
    },
}
celery.conf.timezone = DEFAULT_TIMEZONE_NAME


@task_prerun.connect
def on_task_prerun(sender, task_id, task, args, kwargs, **_):
    structlog.contextvars.bind_contextvars(
        task_id=task_id,
        task_name=task.name,
    )


@setup_logging.connect
def receiver_setup_logging(loglevel, logfile, format, colorize, **kwargs):
    loki_config = setup_loki_config(settings.run_level)
    setup_logger(log_level=loglevel, run_level=settings.run_level, loki_config=loki_config)


@celery.on_after_configure.connect
def init_di_container(sender, **kwargs) -> None:
    container = WorkerContainer()
    container.wire(
        modules=[
            __name__,
            "apps.ag.tasks",
            "apps.bot.tasks",
        ]
    )
