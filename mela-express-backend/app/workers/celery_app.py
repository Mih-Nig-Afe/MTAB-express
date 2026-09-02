"""Celery application factory."""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "mela_express",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Addis_Ababa",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    imports=[
        "app.workers.notification_tasks",
        "app.workers.payment_tasks",
        "app.workers.alert_tasks",
        "app.workers.pdf_tasks",
        "app.workers.flight_tasks",
    ],
)

# Import beat schedule
from app.workers.beat_schedule import CELERY_BEAT_SCHEDULE
celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
