from celery import Celery
from config import settings
from celery.schedules import crontab

celery_app = Celery(
    "tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=["tasks"],
)

celery_app.conf.timezone = "UTC"

celery_app.conf.beat_schedule = {
    'delete-unverified-users': {
        'task': 'tasks.delete_unverified_users',
        'schedule': 30.0,
    },
}

