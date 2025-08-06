import html
import re
from datetime import datetime
import aiohttp
from jsonpath_ng import jsonpath, parse
# import hjson
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
        # print(json_data)
        
        return _x if _x else default

    # def j_extract(json_data, path, default=None) -> list:
    #     """Extract value from json_data using jsonpath"""
    #     jsonpath_expr = parse(path)
    #     result = [match.value for match in jsonpath_expr.find(json_data)]
    #     return result if result else default

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


