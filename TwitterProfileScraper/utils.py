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
        """j_extract"""
        _x = jsonpath(json_data, path)
        return _x if _x else default

    def j_extract_first(self, json_data, path, default=None):
        """j_extract_first"""
        for _x in self.j_extract(json_data, path, default=default) or []:
            return _x
        return default

    def extract_tco_links(self, text):
        """
        Extracts all links starting with 'https://t.co' from the given text and returns them as a single string.

        :param text: The input text containing potential 'https://t.co' links.
        :return: A string containing all extracted links, separated by spaces.
        """
        regex = r"https://t\.co/\S+"
        links = re.findall(regex, text)

        # Join the list of links into a single string separated by spaces
        return ', '.join(links)

    def normalize_text(self, text):
        text = html.unescape(text)
        text = text.encode('utf-8').decode('utf-8')
        text = text.strip().replace("\n", " ").replace("\xa0", " ")
        text = re.sub(r'https://t\.co/\S+', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def convert_timestamp(self, timestamp):
        """
        Converts a timestamp from the format 'Tue Aug 06 02:54:02 +0000 2024' to 'd-m-y h:m:s'.

        :param timestamp: The input timestamp string.
        :return: A string in the format 'd-m-y h:m:s'.
        """
        # Parse the input timestamp string into a datetime object

        dt = datetime.strptime(timestamp, "%a %b %d %H:%M:%S %z %Y")

        # Format the datetime object into the desired format
        return dt.strftime("%d-%m-%Y %H:%M:%S")

    def contains_keywords(self, text, keywords):
        return any(keyword.lower() in text.lower() for keyword in keywords)

    def load_keywords(self, file_path):
        with open(file_path, 'r') as file:
            keywords = file.read().splitlines()
        return keywords

    def convert_to_timestamp(self,date_str):
        # Convert the given string to a datetime object
        dt = datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
        # Format the datetime object into 'd-m-y h:m:s' format
        return dt.strftime("%d-%m-%Y %H:%M:%S")

    def remove_tags_and_links(self, text):
        if not isinstance(text, str):
            return ""

        # First unescape any HTML entities
        text = html.unescape(text)

        # Handle unicode escape sequences
        try:
            text = bytes(text, "latin-1").decode("utf-8", "replace")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

        # Basic cleanups
        text = re.sub(r'RT @\w+:', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'https?://\S+', '', text)

        # Handle other special characters
        text = text.replace('\n', ' ')
        text = text.replace('\r', ' ')
        text = text.replace('\t', ' ')

        # Remove zero-width characters
        text = re.sub(r'[\u200b-\u200f\u2028-\u202f\u205f-\u206f]', '', text)

        # Normalize whitespace
        text = ' '.join(text.split())

        return text.strip()

    def extract_usernames_from_queries(self,queries):
        usernames = []
        for query in queries:
            if query['type'] == 'profile':
                usernames.append(query['user_name'].lstrip('@'))
        return usernames


