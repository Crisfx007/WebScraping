import html
import re
from datetime import datetime
import aiohttp
from jsonpath_ng import jsonpath, parse
import hjson
import requests
from jsonpath import jsonpath
from typing import Dict, Union, List

class ScrapingUtils:
    async def make_async_requests(self, url, headers, params):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                try:
                    # Ensure proper encoding of response
                    response.encoding = 'utf-8'
                    response_text = await response.text()
                    return await response.json()
                except aiohttp.client_exceptions.ContentTypeError as e:
                    print(f"ContentTypeError: {e.message}, URL: {e.request_info.url}")
                    return None
                except Exception as e:
                    print(f"Error: {e}")
                    return None

    @staticmethod
    def j_extract(json_data, path, default=None) -> List:
        """j_extract with Unicode support"""
        _x = jsonpath(json_data, path)
        return _x if _x else default

    def j_extract_first(self, json_data, path, default=None):
        """j_extract_first with Unicode support"""
        for _x in self.j_extract(json_data, path, default=default) or []:
            return _x
        return default

    def extract_tco_links(self, text):
        """Extract t.co links with Unicode support"""
        if not isinstance(text, str):
            return ""
        regex = r"https://t\.co/\S+"
        links = re.findall(regex, text)
        return ', '.join(links)

    def normalize_text(self, text):
        """Normalize text while preserving non-English characters"""
        if not isinstance(text, str):
            return ""
            
        # Unescape HTML entities while preserving Unicode
        text = html.unescape(text)
        
        # Handle common Twitter text artifacts
        text = text.replace("\n", " ")
        text = text.replace("\r", " ")
        text = text.replace("\t", " ")
        
        # Remove URLs but keep the rest of the text intact
        text = re.sub(r'https://t\.co/\S+', '', text)
        
        # Normalize whitespace while preserving Unicode characters
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def convert_timestamp(self, timestamp):
        """Convert timestamp with Unicode support"""
        try:
            dt = datetime.strptime(timestamp, "%a %b %d %H:%M:%S %z %Y")
            return dt.strftime("%d-%m-%Y %H:%M:%S")
        except ValueError as e:
            print(f"Error converting timestamp: {e}")
            return None

    def contains_keywords(self, text, keywords):
        """Check keywords with Unicode support"""
        if not isinstance(text, str):
            return False
        return any(keyword.lower() in text.lower() for keyword in keywords)

    def load_keywords(self, file_path):
        """Load keywords with Unicode support"""
        with open(file_path, 'r', encoding='utf-8') as file:
            keywords = file.read().splitlines()
        return keywords

    def remove_tags_and_links(self, text):
        """Clean text while preserving non-English characters"""
        if not isinstance(text, str):
            return ""

        # Unescape HTML entities
        text = html.unescape(text)

        # Remove Twitter-specific patterns
        text = re.sub(r'RT @\w+:', '', text)  # Remove retweet markers
        text = re.sub(r'@(\w+)', r'\1', text)  # Remove '@' but keep the username
        text = re.sub(r'https?://\S+', '', text)  # Remove URLs
        text = re.sub(r'#(\w+)', r'\1', text)  # Remove '#' but keep the word

        # Remove zero-width and invisible characters while keeping other Unicode
        text = re.sub(r'[\u200b-\u200f\u2028-\u202f\u205f-\u206f]', '', text)

        # Normalize whitespace while preserving Unicode characters
        text = ' '.join(text.split())

        return text.strip()

    def extract_usernames_from_queries(self, queries):
        """Extract usernames with Unicode support"""
        usernames = []
        for query in queries:
            if query['type'] == 'profile':
                usernames.append(query['user_name'].lstrip('@'))
        return usernames

