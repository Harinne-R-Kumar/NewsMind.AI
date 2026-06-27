from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def utc_to_ist(dt):
    if dt is None:
        return ""

    if dt.tzinfo is None:
        from datetime import timezone
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(IST)


def format_ist(dt):
    return utc_to_ist(dt).strftime("%d %b %Y • %I:%M %p IST")