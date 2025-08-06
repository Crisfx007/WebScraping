import json
import asyncio
from datetime import datetime
import aiohttp
import os
import csv
import time
import random
from functools import wraps
from dotenv import load_dotenv
from utils import ScrapingUtils
import re



def retry_with_backoff(retries=3, backoff_in_seconds=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise e
                    wait_time = (backoff_in_seconds * (2 ** x)) + random.uniform(0, 1)
                    print(f"Attempt {x + 1} failed. Retrying in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                    x += 1

        return wrapper

    return decorator


class RateLimiter:
    def __init__(self, calls_per_second=10):
        self.calls_per_second = calls_per_second
        self.last_reset = time.time()
        self.calls = 0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            current_time = time.time()
            if current_time - self.last_reset >= 1:
                self.calls = 0
                self.last_reset = current_time

            if self.calls >= self.calls_per_second:
                wait_time = 1 - (current_time - self.last_reset)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                self.calls = 0
                self.last_reset = time.time()

            self.calls += 1


class TwitterScraper(ScrapingUtils):
    def __init__(self, base_url, headers, output_file="ReheSamay.csv"):
        self.base_url = base_url
        self.headers = headers
        self.output_file = output_file
        self.rate_limiter = RateLimiter(calls_per_second=10)
        self.initialize_csv()

    def save_to_json(self, data: dict, filepath: str = "ReheSamay.json") -> None:
        try:
            existing_data = []
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        print("Error reading existing file, starting fresh")
                        existing_data = []

            cleaned_data = self.clean_json_data(data)
            existing_data.append(cleaned_data)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f,
                          ensure_ascii=False,
                          indent=2,
                          default=str)

        except Exception as e:
            print(f"Error saving data: {str(e)}")

    def clean_json_data(self, data: dict) -> dict:
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, str):
                cleaned[key] = self.clean_text(value)
            elif isinstance(value, (list, dict)):
                try:
                    if isinstance(value, str):
                        value = json.loads(value)
                    cleaned[key] = value
                except json.JSONDecodeError:
                    cleaned[key] = value
            else:
                cleaned[key] = value
        return cleaned

    import re

    def clean_text(self, text: str) -> str:
        if not isinstance(text, str):
            return str(text) if text is not None else ""
        try:
            text = bytes(text, "latin-1").decode("utf-8", "replace")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }
        for entity, char in html_entities.items():
            text = text.replace(entity, char)

        # Remove hashtags (words starting with #)
        text = re.sub(r'#\S+', '', text)

        # Additional cleanup
        text = text.replace('\\', '')
        text = text.replace('\x00', '')
        text = text.replace('\\"', '"')
        text = ' '.join(text.split())

        return text.strip()
    def initialize_csv(self):
        headers = [
            'district', 'uuid', 'tweet_id', 'content', 'datetime',
            'likes', 'shares', 'views', 'source', 'media',
            'username', 'url', 'comments'
        ]
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

    @retry_with_backoff(retries=3)
    async def make_api_request(self, url, headers, params):
        await self.rate_limiter.acquire()
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 429:
                    raise Exception("Rate limit exceeded")
                return await response.json()

    async def get_user_id_from_twitter(self, username):
        url = "https://twitter241.p.rapidapi.com/user"
        querystring = {"username": username}
        try:
            response = await self.make_api_request(url, self.headers, querystring)
            if response:
                try:
                    rest_id = response['result']['data']['user']['result']['rest_id']
                    print(f"User ID (rest_id) for {username}: {rest_id}")
                    return rest_id
                except KeyError as e:
                    print(f"Key error: {e}")
                    return None
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None

    async def search_tweets(self, querystring, cursor=None):
        if cursor:
            querystring['cursor'] = cursor
            print(querystring)
        try:
            content_json = await self.make_api_request(self.base_url, self.headers, querystring)
            if content_json is None:
                print("Failed to fetch tweets")
            return content_json
        except Exception as e:
            print(f"Error in search_tweets: {e}")
            return None

    async def fetch_comments(self, querystring, cursor=None):
        if cursor:
            querystring['cursor'] = cursor
        comments_url = "https://twitter241.p.rapidapi.com/comments"
        try:
            return await self.make_api_request(comments_url, self.headers, querystring)
        except Exception as e:
            print(f"Error fetching comments: {e}")
            return None

    async def process_user(self, user_id, index, tenant_id, district, is_comp, comp_id=None):
        if not user_id:
            print("Invalid user_id")
            return

        querystring = {"user": user_id, "count": "200"}
        cursor1 = None
        retry_count = 0
        max_retries = 3

        for k in range(2):
            while retry_count < max_retries:
                try:
                    content_json = await self.search_tweets(querystring, cursor1)
                    if not content_json:
                        retry_count += 1
                        await asyncio.sleep(1)
                        continue

                    cursor1 = self.j_extract_first(content_json, "cursor.bottom")
                    content_json_filtered = self.j_extract(content_json, "result.timeline.instructions[1].entries.*")

                    if not content_json_filtered:
                        content_json_filtered = self.j_extract_first(content_json,
                                                                     "result.timeline.instructions[0].entries")
                    if not content_json_filtered:
                        content_json_filtered = self.j_extract_first(content_json,
                                                                     "result.timeline.instructions[2].entries")

                    if content_json_filtered:
                        for entry in content_json_filtered[:-1]:
                            try:
                                tweet_data = await self.extract_tweet_data(entry)
                                if tweet_data:
                                    print(f"Tweet {tweet_data['id']} crawled")
                                    comm = []
                                    tweet_id = tweet_data['id']

                                    if tweet_id:
                                        querystring2 = {"pid": tweet_id, "count": "100", "rankingMode": "Relevance"}
                                        cursor2 = None

                                        for _ in range(500):
                                            try:
                                                comments = await self.fetch_comments(querystring2, cursor2)
                                                cursor2 = self.j_extract_first(comments, "cursor.bottom")

                                                if _ == 3 and cursor2 is None:
                                                    break

                                                comments = self.j_extract(comments, "result.instructions[0].entries.*")
                                                if not comments:
                                                    print("No comments found")
                                                    break

                                                if comments:
                                                    for c in comments[1:-1]:
                                                        try:
                                                            result = await self.extract_comment_data(c)
                                                            if result:
                                                                comm.append(result)
                                                                print(f"Comment on Tweet {tweet_id} crawled")
                                                        except Exception as e:
                                                            print(f"Error processing comment: {str(e)}")
                                                            continue

                                            except Exception as e:
                                                print(f"Error fetching comments for Tweet {tweet_id}: {e}")
                                                continue

                                    csv_data = {
                                        'tweet_id': tweet_data["id"],
                                        'content': self.clean_text(tweet_data["content"]),
                                        'datetime': tweet_data["datetime"],
                                        'likes': tweet_data["likes"],
                                        'shares': tweet_data["shares"],
                                        'views': tweet_data["views"],
                                        'source': tweet_data["source"],
                                        'isBlue': tweet_data['is_blueTick'],
                                        "followers": tweet_data["followers"],
                                        "hashtags": tweet_data["hashtags"],
                                        "user_mentions": tweet_data["user_mentions"],
                                        'media': tweet_data["media"],
                                        'username': tweet_data["username"],
                                        'url': f"https://x.com/{tweet_data['username']}/status/{tweet_data['id']}",
                                        'comments': comm
                                    }
                                    self.save_to_json(data=csv_data, filepath="ReheSamay.json")

                            except Exception as e:
                                print(f"Error processing tweet: {e}")
                                continue

                    print(f"Batch complete - 20 tweets - {k}")
                    if cursor1 is None:
                        break

                    break  # Break the retry loop if successful
                except Exception as e:
                    print(f"Error in batch {k}, attempt {retry_count + 1}: {e}")
                    retry_count += 1
                    if retry_count < max_retries:
                        await asyncio.sleep(1)
                    continue


    async def extract_tweet_data(self, c):
        try:
            content = self.j_extract_first(c, "content.itemContent.tweet_results.result.legacy.full_text")
            content = self.remove_tags_and_links(content) if content else None
            idd = self.j_extract_first(c, "content.itemContent.tweet_results.result.legacy.id_str")

            if not (content and idd):
                return None

            tweet_datetime = self.j_extract_first(c, "content.itemContent.tweet_results.result.legacy.created_at")
            if tweet_datetime:
                tweet_datetime = self.convert_timestamp(tweet_datetime)

            username = self.j_extract_first(c,
                                            "content.itemContent.tweet_results.result.core.user_results.result.legacy.screen_name")
            source = "TWITTER"

            media = self.j_extract(c,
                                   "content.itemContent.tweet_results.result.legacy.entities.media[*].media_url_https")
            likes = int(self.j_extract_first(c, "content.itemContent.tweet_results.result.legacy.favorite_count") or 0)
            shares = int(self.j_extract_first(c, "content.itemContent.tweet_results.result.legacy.retweet_count") or 0)
            views = self.j_extract_first(c, "content.itemContent.tweet_results.result.views.count")
            is_blue = self.j_extract_first(c,
                                           "content.itemContent.tweet_results.result.core.user_results.result.is_blue_verified")
            followers = int(self.j_extract_first(c,
                                                 "content.itemContent.tweet_results.result.core.user_results.result.legacy.followers_count") or 0)

            if views:
                views = int(views)

            hashtags = self.j_extract(c, "content.itemContent.tweet_results.result.legacy.entities.hashtags[*].text")
            user_mentions = self.j_extract(c,
                                           "content.itemContent.tweet_results.result.legacy.entities.user_mentions.*")
            user_mention_list = []

            if user_mentions:
                for mention in user_mentions:
                    try:
                        name = mention["name"]
                        screen_name = mention["screen_name"]
                        user_mention_list.append({"name": name, "screen_name": screen_name})
                    except KeyError:
                        continue

            return {
                "id": idd,
                "content": content,
                "datetime": tweet_datetime,
                "likes": likes,
                "shares": shares,
                "views": views,
                "source": source,
                "media": media,
                "username": username,
                "is_blueTick": is_blue,
                "followers": followers,
                "hashtags": hashtags,
                "user_mentions": user_mention_list
            }
        except Exception as e:
            print(f"Error in extract_tweet_data: {e}")
            return None

    async def extract_comment_data(self, c):
        try:
            content = self.j_extract_first(c, "content.items[0].item.itemContent.tweet_results.result.legacy.full_text")
            if not content:
                return None

            content = self.remove_tags_and_links(content)
            media = self.j_extract(c,
                                   "content.items[0].item.itemContent.tweet_results.result.legacy.entities.media[*].media_url_https")
            likes = int(self.j_extract_first(c,
                                             "content.items[0].item.itemContent.tweet_results.result.legacy.favorite_count") or 0)
            shares = int(self.j_extract_first(c,
                                              "content.items[0].item.itemContent.tweet_results.result.legacy.retweet_count") or 0)
            views = self.j_extract_first(c, "content.items[0].item.itemContent.tweet_results.result.views.count")
            is_blue = self.j_extract_first(c,
                                           "content.items[0].item.itemContent.tweet_results.result.core.user_results.result.is_blue_verified")
            followers = int(self.j_extract_first(c,
                                                 "content.items[0].item.itemContent.tweet_results.result.core.user_results.result.legacy.followers_count") or 0)

            if views:
                views = int(views)

            return {
                "content": self.clean_text(content),
                "likes": likes,
                "shares": shares,
                "views": views,
                "is_blueTick": is_blue,
                "followers": followers
            }
        except Exception as e:
            print(f"Error in extract_comment_data: {e}")
            return None

    async def main(self):
        try:
            user_id = await self.get_user_id_from_twitter("ReheSamay")
            if user_id:
                await self.process_user(user_id, "1", "1", "1", "1", "1")
            else:
                print("Failed to get user ID")
        except Exception as e:
            print(f"Error in main: {e}")


if __name__ == "__main__":
    headers = {
	"x-rapidapi-key": "",
	"x-rapidapi-host": "twitter241.p.rapidapi.com"
}

    scraper = TwitterScraper(
        base_url="https://twitter241.p.rapidapi.com/user-tweets",
        headers=headers
    )

    asyncio.run(scraper.main())