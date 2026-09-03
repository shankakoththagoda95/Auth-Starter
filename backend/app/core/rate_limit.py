from slowapi import Limiter
from slowapi.util import get_remote_address

# For local development this uses memory. Before scaling to multiple API servers,
# configure SlowAPI with Redis so every server shares the same counters.
limiter = Limiter(key_func=get_remote_address, default_limits=[])
