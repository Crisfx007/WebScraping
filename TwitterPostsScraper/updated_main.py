import requests
import json
import asyncio
from datetime import datetime
import aiohttp
import os
import csv
import re
from utils import ScrapingUtils

class TwitterScraper(ScrapingUtils):

    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers

    def remove_tags_and_links(self, text):
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'https://t\.co/\S+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = text.replace("\n", " ").replace("\xa0", " ")
        return text.strip()

    def get_user_id_from_twitter(self, username):
        url = "https://twitter241.p.rapidapi.com/user"
        querystring = {"username": username}

        response = requests.get(url, headers=self.headers, params=querystring)
        if response.status_code == 200:
            # Print the JSON response
            data = response.json()
            # print(f"JSON response for {username}: {data}")  # Added print statement to show the entire JSON

            try:
                rest_id = data['result']['data']['user']['result']['rest_id']
                print(f"User ID (rest_id) for {username}: {rest_id}")
                return rest_id
            except KeyError as e:
                print(f"Key error: {e} - Expected key path was not found in the response.")
                return None
        else:
            print(f"Failed to get user info for {username}, status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None


    async def search_tweets(self, querystring, cursor=None):
        if cursor:
            querystring['cursor'] = cursor
            print(querystring)
        content_json = await self.make_async_requests(self.base_url, headers=self.headers, params=querystring)
        if content_json is None:
            print("Failed to fetch tweets")
        return content_json

    def save_tweets_to_csv(self, tweets, username):
        filename = f"{username}"
        header = ["id", "content", "datetime", "likes", "shares", "views", "source", "username"]
        file_exists = os.path.isfile(filename)
        with open(filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=header)
            if not file_exists:
                writer.writeheader()
            for tweet in tweets:
                writer.writerow(tweet)
        print(f"Saved tweets to {filename}")

    async def process_user(self, user_id, username):
        querystring = {"user": user_id, "count": "100"}
        cursor = None
        for k in range(2):
            content_json = await self.search_tweets(querystring, cursor)
            cursor = self.j_extract_first(content_json, "cursor.bottom")
            content_json_filtered = self.j_extract(content_json, "result.timeline.instructions[1].entries.*")
            if not content_json_filtered:
                content_json_filtered = self.j_extract_first(content_json, "result.timeline.instructions[0].entries")

            if content_json_filtered:
                for entry in content_json_filtered[:-1]:
                    try:
                        tweet_data = self.extract_tweet_data(entry)
                        if tweet_data:
                            print(f"Tweet {tweet_data['id']} crawled")
                            comm = []
                            tweet_id = tweet_data['id']
                            cursor2 = None
                            if tweet_id:
                                querystring2 = {"pid": tweet_id, "count": "100", "rankingMode": "Relevance"}

                            self.save_tweets_to_csv([tweet_data], f"{username}.csv")
                            print(f"Tweet {tweet_data['id']} saved")
                    except Exception as e:
                        print(f"Error processing tweet: {e}")
                        continue

                # Only print the batch completion message if content_json_filtered has elements
                print(f"Batch complete - {len(content_json_filtered) - 1} tweets - {k}")

            else:
                # If content_json_filtered is None, print a message and break the loop
                print("No tweets found or issue with content structure.")
                break

            if cursor is None:
                break


    def extract_tweet_data(self, entry):
        content = self.j_extract_first(entry, "content.itemContent.tweet_results.result.legacy.full_text")
        if content:
            content = self.remove_tags_and_links(content)
        tweet_id = self.j_extract_first(entry, "content.itemContent.tweet_results.result.rest_id")
        created_at = self.j_extract_first(entry, "content.itemContent.tweet_results.result.legacy.created_at")
        likes = self.j_extract_first(entry, "content.itemContent.tweet_results.result.legacy.favorite_count")
        views = self.j_extract_first(entry, "content.itemContent.tweet_results.result.views.count")
        retweet = self.j_extract_first(entry, "content.itemContent.tweet_results.result.legacy.retweet_count")
        quote_rt = self.j_extract_first(entry, "content.itemContent.tweet_results.result.legacy.quote_count")
        shares = int(retweet or 0) + int(quote_rt or 0)
        source = "TWITTER"
        username = self.j_extract_first(entry, "content.itemContent.tweet_results.result.core.user_results.result.legacy.screen_name")

        if content and tweet_id:
            return {
                "id": tweet_id,
                "content": content,
                "datetime": self.convert_timestamp(created_at),
                "likes": likes,
                "shares": shares,
                "views": views,
                "source": source,
                "username": username
            }
        return None

    async def main(self, usernames):
        for username in usernames:
            user_id = self.get_user_id_from_twitter(username)
            if user_id:
                await self.process_user(user_id, username)

if __name__ == "__main__":
    headers = {
        "x-rapidapi-key": "",
        "x-rapidapi-host": "twitter241.p.rapidapi.com"
    } 

    scraper = TwitterScraper(
        base_url="https://twitter241.p.rapidapi.com/user-tweets",
        headers=headers
    )

    # List of usernames to scrape data for
    # usernames = ["RahulGandhi","priyankagandhi", "INCIndia","Pawankhera","SupriyaShrinate","Jairam_Ramesh","KapilSibal",
    #              "AbhijitRajINC","mayur_jha","kharge","adhirrcinc","ShashiTharoor","PChidambaram_IN","SachinPilot",
    #              "rssurjewala","DrRameshwarOra1","mahuamajilive","HemantSorenJMM"]  # Add more usernames as needed

    usernames=[""]
    asyncio.run(scraper.main(usernames))
