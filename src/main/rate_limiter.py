import os
import time
import threading
from fastapi import HTTPException, status

RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "120"))

_lock = threading.Lock()
# structure: { tenant: (window_start_epoch_minute, count) }
_counters = {}

def _current_window():
    return int(time.time() // 60)

def check_rate_limit(tenant: str):
    """
    Simple in-memory fixed window rate limiter.
    Raises HTTPException(429) if limit exceeded.
    """
    if RATE_LIMIT_PER_MIN <= 0:
        return
    now = _current_window()
    with _lock:
        window, count = _counters.get(tenant, (now, 0))
        if window != now:
            # reset window
            window, count = now, 0
        if count + 1 > RATE_LIMIT_PER_MIN:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate limit exceeded")
        _counters[tenant] = (window, count + 1)
