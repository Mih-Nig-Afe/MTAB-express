"""
Notification Celery tasks.
send_telegram_notification, send_sms_notification, bulk_arrival_notifications
Retries 3x with exponential backoff; writes NotificationLog rows.
"""
# TODO: implement (Task 13.2)
