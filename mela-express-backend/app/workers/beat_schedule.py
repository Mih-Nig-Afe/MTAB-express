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
    "poll-active-flights": {
        "task": "app.workers.flight_tasks.poll_active_flights",
        "schedule": crontab(minute="*/10"),
    },
    "pickup-reminders": {
        "task": "app.workers.alert_tasks.send_pickup_reminders",
        "schedule": crontab(hour=6, minute=0),  # 09:00 EAT
    },
}
