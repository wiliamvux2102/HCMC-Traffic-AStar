"""ISO timestamps normalized to Vietnam's UTC+07:00 timezone."""

from datetime import datetime, timedelta, timezone

LOCAL_TIMEZONE = timezone(timedelta(hours=7), name="Asia/Ho_Chi_Minh")


def parse_timestamp(value):
    timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=LOCAL_TIMEZONE)
    return timestamp.astimezone(LOCAL_TIMEZONE)


def normalize_timestamp(value):
    return parse_timestamp(value).isoformat()
