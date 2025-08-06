import html
import re
from datetime import datetime
import aiohttp
from jsonpath_ng import jsonpath, parse
import requests
from typing import Dict, Union, List

class ScrapingUtils:
    async def make_async_requests(self, url, headers, params):
        """Makes asynchronous requests to the provided URL."""
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
        """Extracts data from JSON using jsonpath."""
        _x = jsonpath(json_data, path)
        return _x if _x else default

    def j_extract_first(self, json_data, path, default=None):
        """Extracts the first match from JSON using jsonpath."""
        for _x in self.j_extract(json_data, path, default=default) or []:
            return _x
        return default

    def extract_tco_links(self, text):
        """
        Extracts all links starting with 'https://t.co' from the given text and returns them as a single string.

        :param text: The input text containing potential 'https://t.co' links.
        :return: A string containing all extracted links, separated by commas.
        """
        regex = r"https://t\.co/\S+"
        links = re.findall(regex, text)

        # Join the list of links into a single string separated by commas
        return ', '.join(links)

    def normalize_text(self, text):
        """Normalizes the given text by cleaning unwanted characters and links."""
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
        dt = datetime.strptime(timestamp, "%a %b %d %H:%M:%S %z %Y")
        return dt.strftime("%d-%m-%Y %H:%M:%S")

    def contains_keywords(self, text, keywords):
        """Checks if any of the given keywords are present in the text."""
        return any(keyword.lower() in text.lower() for keyword in keywords)

    def load_keywords(self, file_path):
        """Loads keywords from a file into a list."""
        with open(file_path, 'r') as file:
            keywords = file.read().splitlines()
        return keywords

    def convert_to_timestamp(self, date_str):
        """Converts the given string to a datetime object and formats it into 'd-m-y h:m:s'."""
        dt = datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
        return dt.strftime("%d-%m-%Y %H:%M:%S")

    def get_user_id_from_twitter(self, username):
        """
        Retrieves the user ID from Twitter using a public API (e.g., RapidAPI).
        :param username: The Twitter username.
        :return: The user ID or None if not found.
        """
        url = "https://twitter241.p.rapidapi.com/user"
        querystring = {"username": username}
        response = requests.get(url, headers=self.headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
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

    def remove_tags_and_links(self, text):
        """
        Removes unwanted text such as URLs, mentions, and extra spaces.
        :param text: The input text to clean.
        :return: The cleaned text.
        """
        text = re.sub(r'RT @:\w+', '', text)  # Remove "RT @" mentions
        text = re.sub(r'@\w+', '', text)  # Remove Twitter handles
        text = re.sub(r'https://t\.co/\S+', '', text)  # Remove 't.co' links
        text = re.sub(r'\s+', ' ', text).strip()  # Normalize spaces
        text = text.strip().replace("\n", " ").replace("\xa0", " ")  # Further cleanup
        return text.strip()

    def extract_usernames_from_queries(self, queries):
        """Extracts relevant usernames from a list of queries."""
        usernames = []
        for query in queries:
            if query['type'] == 'profile':
                usernames.append(query['user_name'].lstrip('@'))
        return usernames


