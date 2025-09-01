# common/config.py

import os

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Redis keys
OPTIMIZATION_RESULT_KEY = "household:optimization_result"
BID_REQUEST_KEY = "household:bid_request"
OFFER_REQUEST_KEY = "household:offer_request"

# General parameters
DEFAULT_TIMEOUT = 5  # seconds
