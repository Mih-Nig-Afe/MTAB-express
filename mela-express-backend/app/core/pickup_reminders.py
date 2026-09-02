"""Ready-for-pickup reminder cadence: daily for 7 days, then stop."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

PICKUP_REMINDER_DAYS = 7
MIN_HOURS_BETWEEN = 20


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def reminder_day_number(ready_at: datetime, now: datetime) -> int:
    """1-based day in the reminder window (day 1 is the ready-for-pickup notice)."""
    delta = _aware(now) - _aware(ready_at)
    return max(1, int(delta.total_seconds() // 86400) + 1)


def reminder_due(
    *,
    ready_at: datetime | None,
    last_sent_at: datetime | None,
    now: datetime,
    already_sent: int = 0,
    picked_up: bool = False,
    max_days: int = PICKUP_REMINDER_DAYS,
) -> bool:
    if picked_up or ready_at is None:
        return False
    if already_sent >= max_days:
        return False
    day = reminder_day_number(ready_at, now)
    if day > max_days:
        return False
    if last_sent_at is None:
        return True
    elapsed = _aware(now) - _aware(last_sent_at)
    if elapsed < timedelta(hours=MIN_HOURS_BETWEEN):
        return False
    return day > already_sent or elapsed >= timedelta(hours=MIN_HOURS_BETWEEN)
