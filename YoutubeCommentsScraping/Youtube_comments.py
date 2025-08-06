import os
import re
import csv
import googleapiclient.discovery
from datetime import datetime, timedelta

# Function to convert ISO 8601 duration to seconds
def iso_duration_to_seconds(iso_duration):
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(iso_duration)

    if not match:
        return 0  # Return 0 or handle the error appropriately

    hours = int(match.group(1) or 0)  # Defaults to 0 if not found
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

# Function to filter videos based on duration and upload date
def filter_videos(videos):
    filtered_videos = []
    six_months_ago = datetime.now() - timedelta(days=182)  # 6 months ago

    for video in videos:
        video_id = video['id']
        duration_seconds = iso_duration_to_seconds(video['contentDetails']['duration'])
        upload_date = video['snippet']['publishedAt']

        # Convert upload date to datetime object
        upload_date = datetime.strptime(upload_date, '%Y-%m-%dT%H:%M:%SZ')

        # Check if the video is longer than 5 minutes and uploaded in the last 6 months
        if duration_seconds > 300 and upload_date > six_months_ago:
            filtered_videos.append(video)

    return filtered_videos

# Function to scrape comments from filtered videos
def scrape_comments_from_filtered_videos(youtube, channel_id):
    # Get videos from the channel
    request = youtube.search().list(
        part='id',
        channelId=channel_id,
        maxResults=50,
        order='date'
    )
    response = request.execute()

    # Get video IDs
    video_ids = [item['id']['videoId'] for item in response['items'] if 'videoId' in item['id']]
    
    # Get video details (including duration)
    request = youtube.videos().list(
        part='contentDetails,snippet',
        id=','.join(video_ids)
    )
    video_details_response = request.execute()
    
    filtered_videos = filter_videos(video_details_response['items'])

    video_comments_data = []
    for video in filtered_videos:
        video_id = video['id']
        video_title = video['snippet']['title']
        video_duration = video['contentDetails']['duration']
        comments = get_comments(youtube, video_id)

        video_comments_data.append({
            'video_id': video_id,
            'title': video_title,
            'duration': video_duration,
            'comments': comments
        })

    return video_comments_data

# Function to get comments from a specific video
def get_comments(youtube, video_id):
    comments = []
    request = youtube.commentThreads().list(
        part='snippet',
        videoId=video_id,
        textFormat='plainText',
        maxResults=100
    )
    
    while request is not None:
        response = request.execute()
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment)
        request = youtube.commentThreads().list_next(request, response)
    
    return comments

# Main function
def main():
    # Set up the YouTube API client
    api_service_name = "youtube"
    api_version = "v3"
    youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey='')

    # Donald Trump's channel ID
    CHANNEL_ID = 'UC0XBsJpPhOLg0k4x9ZwrWzw'  # Replace with actual channel ID
    video_comments_data = scrape_comments_from_filtered_videos(youtube, CHANNEL_ID)

    # Save data to a JSON file
    with open('Harris_6NOV_Youtube.csv', 'w', newline='', encoding='utf-8') as f:
        # Create a csv writer object
        writer = csv.DictWriter(f, fieldnames=video_comments_data[0].keys())
        
        # Write the header (column names)
        writer.writeheader()
        
        # Write the rows of data
        writer.writerows(video_comments_data)

        print("Data saved to Harris_video_comments.csv")

if __name__ == "__main__":
    main()