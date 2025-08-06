import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
BASE_URL = "https://twitter241.p.rapidapi.com/search-v2"  # Changed from TWITTER_API_BASE_URL
COMMENTS_URL = "https://twitter241.p.rapidapi.com/comments"  # Changed from TWITTER_COMMENTS_URL

# API Headers
HEADERS = {
    "x-rapidapi-key": os.getenv("RAPID_API_KEY"),
    "x-rapidapi-host": "twitter241.p.rapidapi.com"
}

# API Rate Limits
RATE_LIMIT_PER_SECOND = 10
MAX_RETRIES = 3
BACKOFF_TIME = 1  # seconds

# Data Storage
DEFAULT_OUTPUT_DIR = "twitter_data"
DEFAULT_FILENAME = "tweets.json"

# Crawling Settings
MAX_COMMENT_PAGES = 5
TWEETS_PER_REQUEST = "1000"
DEFAULT_SEARCH_TYPE = "Latest"