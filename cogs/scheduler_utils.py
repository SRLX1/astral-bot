from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo

def compute_next_send(send_time: str, tz_name: str) -> int:
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    h, m = map(int, send_time.split(":"))
    target = datetime.combine(now.date(), dt_time(h, m), tzinfo=tz)
    if target <= now:
        target = datetime.combine(now.date() + timedelta(days=1), dt_time(h, m), tzinfo=tz)
    return int(target.timestamp())