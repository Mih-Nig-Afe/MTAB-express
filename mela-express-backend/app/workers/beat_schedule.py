from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "retry-failed-webhooks": {
        "task": "app.workers.payment_tasks.retry_failed_webhook",
        "schedule": crontab(minute="*/15"),  # every 15 minutes
    },
    "check-transit-delays": {
        "task": "app.workers.alert_tasks.check_transit_delays",
        "schedule": crontab(minute=0),  # every hour
    },
    "daily-manager-digest": {
        "task": "app.workers.alert_tasks.daily_manager_digest",
        "schedule": crontab(hour=4, minute=0),  # 07:00 EAT = 04:00 UTC
    },
}
