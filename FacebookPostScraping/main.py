import requests
from jsonpath_ng import parse
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()
import csv
url = "https://facebook-scraper3.p.rapidapi.com/page/posts"

querystring = {"page_id": "100006654819971"}

headers = {
    "x-rapidapi-key": "",
    "x-rapidapi-host": "facebook-scraper3.p.rapidapi.com",
}

def convert_timestamp_to_datetime(timestamp):
    # Convert the timestamp to a datetime object
    dt_object = datetime.fromtimestamp(timestamp)
    # Format the datetime object into the desired format
    return dt_object.strftime("%d-%m-%Y %H:%M:%S")

for i in range(5):
    response = requests.get(url, headers=headers, params=querystring)

    # Check for successful response
    if response.status_code == 200:
        # Parse the JSON response
        json_data = response.json()

        # Use JSONPath to extract data
        jsonpath_exp = parse("$.results[*]")  # Use a JSONPath expression to target the required data
        matches = jsonpath_exp.find(json_data)

        # Extract and process matched data
        extracted_data = [match.value for match in matches]
        for d in extracted_data:
            date = convert_timestamp_to_datetime(d.get("timestamp")) if d.get("timestamp") else None

            # Safely check if 'album_preview' exists and if it's a list with an item
            album_preview = d.get("album_preview")
            media_url = None
            if album_preview and isinstance(album_preview, list) and len(album_preview) > 0:
                media_url = album_preview[0].get("image_file_uri")

            document = {
                "district": "Colombo",
                "uuid": "cf5315e2-8bc4-58cd-9820-07b0704ec5db",
                "news": [
                    {
                        "id": d.get("post_id"),
                        "content": d.get("message"),
                        "datetime": date,
                        "heading": "",
                        "media": [media_url],  # Use the safe media URL
                        "likes": d.get("reactions_count"),
                        "shares": d.get("reshare_count"),
                        "source": "FACEBOOK",
                        "username": d.get("author", {}).get("name"),
                        "url": d.get("url"),
                        "views": d.get("reactions_count"),
                        "comments": []
                    }
                ]
            }

            # Index the document in Elasticsearch
            # es.index(index="jharkhand_raw_data", id=d.get("post_id"), body=document, op_type='index')

        # Check for cursor to fetch the next set of data
        cursor = json_data.get("cursor")
        if cursor:
            querystring["cursor"] = cursor  # Add the cursor to the query for the next request
        else:
            print("No more data available.")
            break
    else:
        print(f"Error: Received status code {response.status_code}")
        break  # This break is for the outer loop
