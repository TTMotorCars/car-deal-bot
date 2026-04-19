"""
Car Deal Bot — Configuration

Edit this file to change what the bot searches for. All secrets (Twilio
keys, eBay/Marketcheck API keys, etc.) live in .env, not here.

You can enable/disable individual sources via .env flags — see .env.example.
"""

# ==============================================================================
# WHAT CARS TO LOOK FOR
# ==============================================================================
SEARCH_QUERIES = [
    "honda civic",
    "toyota corolla",
    "toyota camry",
    "mazda 3",
    "mazda3",
    "hyundai elantra",
]

MAX_PRICE = 10000
MIN_PRICE = 1500
MIN_YEAR = 2008
MAX_MILES = 180000    # set to None to disable

# ==============================================================================
# DEAL DETECTION
# ==============================================================================
DEAL_THRESHOLD_PERCENT = 0.15
MIN_COMPS_FOR_MEDIAN = 5
INSTANT_FLAG_UNDER = 4000

# ==============================================================================
# CRAIGSLIST REGIONS
# ==============================================================================
CRAIGSLIST_REGIONS = [
    # Illinois
    "chicago", "peoria", "springfieldil", "rockford", "decatur",
    "bn", "chambana", "quadcities", "carbondale", "lasalle", "mattoon",
    # Wisconsin
    "milwaukee", "madison", "racine",
    # Indiana
    "indianapolis", "fortwayne", "evansville", "bloomington",
    # Iowa
    "desmoines", "cedarrapids", "iowacity",
    # Missouri
    "stlouis",
    # Kentucky
    "louisville",
]
CRAIGSLIST_REGIONS = list(dict.fromkeys(CRAIGSLIST_REGIONS))

# ==============================================================================
# EBAY MOTORS + CARMAX/CARVANA/MARKETCHECK CENTROID
# ==============================================================================
# All distance-based sources center on this zip.
EBAY_ENABLED = True
EBAY_ZIP_CODE = "60601"
EBAY_MAX_DISTANCE_MILES = 400

# ==============================================================================
# GENERIC RSS FEEDS (optional — add any you like)
# ==============================================================================
# Example entries you can uncomment or add to:
#
# GENERIC_RSS_FEEDS = [
#   {"label": "my-favorite-dealer", "url": "https://example-dealer.com/feed.rss"},
#   {"label": "forum-fs",           "url": "https://honda-forum.example/fs.rss"},
# ]
GENERIC_RSS_FEEDS = []

# ==============================================================================
# NOTIFICATION THROTTLING
# ==============================================================================
MAX_ALERTS_PER_RUN = 15
DEDUPE_DB_PATH = "seen_listings.db"

# ==============================================================================
# HTTP BEHAVIOR
# ==============================================================================
REQUEST_TIMEOUT_SECONDS = 20
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)
POLITE_DELAY = 1.5
