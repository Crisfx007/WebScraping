import aiohttp
from typing import Dict, Optional, Any
from config.settings import BASE_URL, COMMENTS_URL, HEADERS
from utils.rate_limiter import RateLimiter
from .scraping_utils import ScrapingUtils

class TwitterAPIClient(ScrapingUtils):
    def __init__(self, headers: Dict[str, str]):
        self.headers = headers
        self.base_url = BASE_URL
        self.comments_url = COMMENTS_URL
        self.rate_limiter = RateLimiter(calls_per_second=1000)


    async def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict]:
        """
        Make API request with rate limiting
        """
        await self.rate_limiter.acquire()
        return await self.make_async_requests(url, self.headers, params)


    async def search_tweets(self, query: str, count: str = "1000",
                            search_type: str = "Latest", cursor: Optional[str] = None) -> Optional[Dict]:
        """
        Search tweets using the Twitter API
        """
        querystring = {
            "type": search_type,
            "count": count,
            "query": query
        }
        if cursor:
            querystring['cursor'] = cursor

        try:
            return await self._make_request(self.base_url, querystring)
        except Exception as e:
            print(f"Error in search_tweets: {e}")
            return None

    async def fetch_comments(self, tweet_id: str, count: str = "100",
                             cursor: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch comments for a specific tweet
        """
        querystring = {
            "pid": tweet_id,
            "count": count,
            "rankingMode": "Relevance"
        }
        if cursor:
            querystring['cursor'] = cursor

        try:
            return await self._make_request(self.comments_url, querystring)
        except Exception as e:
            print(f"Error fetching comments: {e}")
            return None