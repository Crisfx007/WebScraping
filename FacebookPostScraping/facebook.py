import requests
from datetime import datetime
from jsonpath_ng import parse
import json
import os

def convert_timestamp_to_datetime(timestamp):
    if isinstance(timestamp, str):
        # If the timestamp is in string format, assume it's in ISO 8601 format
        try:
            dt_object = datetime.fromisoformat(timestamp)  # Adjust to your timestamp format if needed
            return dt_object.strftime("%d-%m-%Y %H:%M:%S")
        except ValueError:
            print(f"Error: Invalid timestamp format: {timestamp}")
            return None
    else:
        # If timestamp is numeric, use fromtimestamp
        dt_object = datetime.fromtimestamp(timestamp)
        return dt_object.strftime("%d-%m-%Y %H:%M:%S")

# Function to save data to a JSON file
def save_to_json(data, filename=".json"):
    try:
        existing_data = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as file:
                try:
                    existing_data = json.load(file)
                except json.JSONDecodeError:
                    print("File exists but is empty or corrupted. Starting fresh.")
        existing_data.append(data)
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving data: {e}")

# API details for posts and comments
posts_url = "https://facebook-scraper3.p.rapidapi.com/page/posts"
comments_url = "https://facebook-scraper3.p.rapidapi.com/post/comments"
headers = {
    "x-rapidapi-key": "",
    "x-rapidapi-host": "facebook-scraper3.p.rapidapi.com"
}
querystring = {"page_id": "100063581806550"}

for i in range(150):
    response = requests.get(posts_url, headers=headers, params=querystring)

    if response.status_code == 200:
        json_data = response.json()
        jsonpath_exp = parse("$.results[*]")  # Extracting all posts
        matches = jsonpath_exp.find(json_data)
        extracted_data = [match.value for match in matches]

        for d in extracted_data:
            # Process post data
            date = convert_timestamp_to_datetime(d.get("timestamp")) if d.get("timestamp") else None
            album_preview = d.get("album_preview")
            media_url = None
            if album_preview and isinstance(album_preview, list) and len(album_preview) > 0:
                media_url = album_preview[0].get("image_file_uri")

            # Prepare document structure
            document = {
                "State": "Delhi",
                "news": [
                    {
                        "id": d.get("post_id"),
                        "content": d.get("message"),
                        "datetime": date,
                        "heading": "",
                        "media": [media_url],
                        "likes": d.get("reactions_count"),
                        "shares": d.get("reshare_count"),
                        "source": "FACEBOOK",
                        "username": d.get("author", {}).get("name"),
                        "url": d.get("url"),
                        "views": d.get("reactions_count"),
                        "comments": []  # Placeholder for comments
                    }
                ]
            }

            post_id = d.get("post_id")
            if post_id:
                # Initialize the cursor for pagination
                comments_cursor = None

                # Fetch comments for the post, with pagination handling
                while True:
                    comment_query = {"post_id": post_id}
                    if comments_cursor:
                        comment_query["cursor"] = comments_cursor
                    
                    comment_response = requests.get(comments_url, headers=headers, params=comment_query)
                    
                    if comment_response.status_code == 200:
                        comments_data = comment_response.json()
                        jsonpath_exp = parse("$.results[*]")  # Extracting all comments for the post
                        matches = jsonpath_exp.find(comments_data)

                        # Process each comment
                        for comment in matches:
                            comment_data = comment.value
                            comment_obj = {
                                "id": comment_data.get("comment_id"),
                                "content": comment_data.get("message"),
                                "author": comment_data.get("from", {}).get("name"),  # 'from' is the key for the author
                                "datetime": convert_timestamp_to_datetime(comment_data.get("created_time")) if comment_data.get("created_time") else None,
                                "likes": comment_data.get("like_count"),
                                "replies": []  # Initialize empty list for replies
                            }

                            # Check if there are replies and process them
                            replies = comment_data.get("replies")
                            if replies and isinstance(replies, list):
                                for reply in replies:
                                    reply_obj = {
                                        "id": reply.get("comment_id"),
                                        "content": reply.get("message"),
                                        "author": reply.get("from", {}).get("name"),
                                        "datetime": convert_timestamp_to_datetime(reply.get("created_time")) if reply.get("created_time") else None,
                                        "likes": reply.get("like_count"),
                                    }
                                    comment_obj["replies"].append(reply_obj)

                            # Add the comment object to the post's comments list
                            document["news"][0]["comments"].append(comment_obj)

                        # Check if there is a next page of comments
                        comments_cursor = comments_data.get("cursor")
                        if not comments_cursor:
                            break  # No more comments to fetch
                    else:
                        print(f"Error fetching comments for Post ID {post_id}: {comment_response.status_code}")
                        break

            # Save the document after processing comments
            save_to_json(document)
            print(f"Processed Post ID: {d.get('post_id')}")

        # Check for the cursor to fetch the next set of data
        cursor = json_data.get("cursor")
        if cursor:
            querystring["cursor"] = cursor
        else:
            print("No more data available.")
            break

    else:
        print(f"Error: Received status code {response.status_code}")
        break

