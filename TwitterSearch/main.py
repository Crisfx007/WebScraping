# main.py

import asyncio
import logging
import json
import os
from typing import Optional, Dict, List
from datetime import datetime

from core.api_client import TwitterAPIClient
from core.data_handler import TwitterDataHandler
from core.extractors import TwitterDataExtractor
from config.settings import HEADERS, BASE_URL, DEFAULT_OUTPUT_DIR
from core.scraping_utils import ScrapingUtils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TwitterCrawler(ScrapingUtils):
    def __init__(self, output_dir: str = "data"):
        self.api_client = TwitterAPIClient(
            {
    "x-rapidapi-key": "",
    "x-rapidapi-host": "twitter241.p.rapidapi.com"
}
        )
        self.extractor = TwitterDataExtractor()
        self.output_file = "LatentSearch.json"

    def save_to_json(self, data: dict, filepath: str = "LatentSearch.json") -> None:
        """Save data to JSON file"""
        try:
            existing_data = []
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        print("Error reading existing file, starting fresh")
                        existing_data = []

            existing_data.append(data)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error saving data: {str(e)}")

    async def process_tweet(self, tweet_content: Dict) -> Optional[str]:
        """Process a single tweet and its comments"""
        try:
            # Extract tweet data
            tweet_data = await self.extractor.extract_tweet_data(tweet_content)
            if not tweet_data:
                return None

            tweet_id = tweet_data['id']
            logger.info(f"Tweet {tweet_id} crawled")

            comm = []

            # If it's not a retweet, fetch comments
            if tweet_id and "RT @" not in tweet_data["content"]:
                comm = await self.process_comments(tweet_id)

            csv_data = {
                'tweet_id': tweet_data["id"],
                'content': tweet_data["content"],
                'datetime': tweet_data["datetime"],
                'likes': tweet_data["likes"],
                'shares': tweet_data["shares"],
                'views': tweet_data["views"],
                'source': tweet_data["source"],
                'isBlue': tweet_data['is_blueTick'],
                "followers": tweet_data["followers"],
                "hashtags": tweet_data["hashtags"],
                "location":"",
                "user_mentions": tweet_data["user_mentions"],
                'media': tweet_data["media"] if tweet_data["media"] else [],
                'username': tweet_data["username"],
                'url': f"https://x.com/{tweet_data['username']}/status/{tweet_data['id']}",
                'comments': comm
            }

            self.save_to_json(data=csv_data)
            return tweet_id

        except Exception as e:
            logger.error(f"Error processing tweet: {e}")
            return None

    async def process_comments(self, tweet_id: str, max_pages: int = 50) -> List[Dict]:
        """Fetch and process comments for a tweet"""
        comments = []
        cursor2 = None
        empty_response_count = 0  # Track empty responses

        for comment_page in range(max_pages):
            if comment_page > 0 and cursor2 is None:
                print(f"No more comments available for tweet {tweet_id}")
                break
            comments_data = await self.api_client.fetch_comments(tweet_id, cursor=cursor2)

            if not comments_data:
                logger.info(f"Empty response for tweet {tweet_id}")
                break  # Break immediately on empty response


            comments_entries = self.j_extract(comments_data, "result.instructions[0].entries.*", default=[])
            if not comments_entries or len(comments_entries) <= 2:  # Accounting for first/last entries
                break


            try:
                querystring2 = {"pid": tweet_id, "count": "100", "rankingMode": "Relevance"}

                cursor2 = self.j_extract_first(comments_data, "cursor.bottom")
                print(f"Comments cursor for tweet {tweet_id}, page {comment_page + 1}: {cursor2}")

                for c in comments_entries[1:-1]:
                    try:
                        result = await self.extractor.extract_comment_data(c)
                        if result:
                            comments.append(result)
                            print(f"Comment on Tweet {tweet_id} crawled")
                    except Exception as e:
                        print(f"Error processing comment: {str(e)}")
                        continue

            except Exception as e:
                print(f"Error fetching comments for Tweet {tweet_id}: {e}")
                continue

        return comments

    async def crawl(self, query: str, max_batches: int = 30):
        """Main crawling function"""
        cursor = None
        processed_tweets = 0

        for batch in range(max_batches):
            try:
                if not cursor and batch > 0:
                    logger.info("No more results available. Stopping crawl.")
                    break

                response = await self.api_client.search_tweets(query, count="1000", search_type="Latest", cursor=cursor)
                if not response:
                    logger.error("No response from API")
                    break

                cursor = self.j_extract_first(response, "cursor.bottom")
                print(f"Using cursor: {cursor}")  # Debug cursor


                content_json_filtered = self.j_extract(response,
                                                       "data.search_by_raw_query.search_timeline.timeline.instructions[0].entries[*]")
                if not content_json_filtered:
                    content_json_filtered = self.j_extract(response,
                                                           "result.timeline.instructions[0].entries.*")
                if not content_json_filtered:
                    logger.error("No tweets found in response")
                    break


                for c in content_json_filtered:
                    if await self.process_tweet(c):
                        processed_tweets += 1

                # If we didn't get cursor earlier, try alternate paths
                if not cursor:
                    cursor = self.j_extract_first(response, "cursor.bottom.value")

                logger.info(f"Current cursor: {cursor}")
                logger.info(f"Processed batch {batch + 1}, total tweets: {processed_tweets}")

            except Exception as e:
                logger.error(f"Error processing batch {batch + 1}: {str(e)}")
                continue

        logger.info(f"Crawling completed. Total tweets processed: {processed_tweets}")



async def main():
    queries = [ "Ranveer Allahbadia @ReheSamay",
               "Samay Raina @BeerBicepsGuy",
               "Apology @BeerBicepsGuy",
               "India's got latent @ReheSamay",]

    crawler = TwitterCrawler(output_dir="twitter_data")

    for query in queries:
        logger.info(f"Processing query: {query}")
        await crawler.crawl(query)
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())