# core/extractors.py
from typing import Dict, List, Optional, Any
from .scraping_utils import ScrapingUtils

class TwitterDataExtractor(ScrapingUtils):
    async def extract_tweet_data(self, c: Dict) -> Optional[Dict]:
        """Extract tweet data using custom json extraction"""
        try:
            content = self.j_extract_first(c, "$..content.itemContent.tweet_results.result.legacy.full_text")
            content = self.remove_tags_and_links(content) if content else None
            idd = self.j_extract_first(c, "$..content.itemContent.tweet_results.result.legacy.id_str")

            tweet_datetime = self.j_extract_first(c, "$..content.itemContent.tweet_results.result.legacy.created_at")
            if tweet_datetime:
                tweet_datetime = self.convert_timestamp(tweet_datetime)

            username = self.j_extract_first(c, "$..content.itemContent.tweet_results.result.core.user_results.result.legacy.screen_name")
            source = "TWITTER"

            media = self.j_extract(c, "$..content.itemContent.tweet_results.result.legacy.entities.media[*].media_url_https")
            likes = int(self.j_extract_first(c, "$..content.itemContent.tweet_results.result.legacy.favorite_count") or 0)
            shares = int(self.j_extract_first(c, "$..content.itemContent.tweet_results.result.legacy.retweet_count") or 0)
            views = self.j_extract_first(c, "$..content.itemContent.tweet_results.result.views.count")
            is_blue = self.j_extract_first(c, "$..content.itemContent.tweet_results.result.core.user_results.result.is_blue_verified")
            followers = int(self.j_extract_first(c, "$..content.itemContent.tweet_results.result.core.user_results.result.legacy.followers_count") or 0)

            if views:
                views = int(views)

            hashtags = self.j_extract(c, "$..content.itemContent.tweet_results.result.legacy.entities.hashtags[*].text")
            user_mentions = self.j_extract(c, "$..content.itemContent.tweet_results.result.legacy.entities.user_mentions.*")
            user_mention_list = []

            if user_mentions:
                for mention in user_mentions:
                    name = mention["name"]
                    screen_name = mention["screen_name"]
                    user_mention_list.append({"name": name, "screen_name": screen_name})

            if content and idd:
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
            return None

        except Exception as e:
            print(f"Error extracting tweet data: {e}")
            return None

    async def extract_comment_data(self, c: Dict) -> Optional[Dict]:
        """Extract comment data using custom json extraction"""
        try:

            content = self.j_extract_first(c, "$..content.items[0].item.itemContent.tweet_results.result.legacy.full_text")
            content = self.remove_tags_and_links(content) if content else None

            media = self.j_extract(c, "$..content.itemContent.tweet_results.result.legacy.entities.media[*].media_url_https")

            likes = int(self.j_extract_first(c, "$..content.items[0].item.itemContent.tweet_results.result.legacy.favorite_count") or 0)
            shares = int(self.j_extract_first(c, "$..content.items[0].item.itemContent.tweet_results.result.legacy.retweet_count") or 0)
            views = self.j_extract_first(c, "$..content.itemContent.tweet_results.result.views.count")

            is_blue = self.j_extract_first(c, "$..content.items[0].item.itemContent.tweet_results.result.core.user_results.result.is_blue_verified")
            followers = self.j_extract_first(c, "$..content.items[0].item.itemContent.tweet_results.result.core.user_results.result.legacy.followers_count")

            if views:
                views = int(views)

            if content:
                return {
                    "content": content,
                    "likes": likes,
                    "shares": shares,
                    "views": views,
                    "media": media,
                    "is_blueTick": is_blue,
                    "followers": followers
                }
            return None

        except Exception as e:
            print(f"Error extracting comment data: {e}")
            return None