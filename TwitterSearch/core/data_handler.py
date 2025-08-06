# core/data_handler.py

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class TwitterDataHandler:
    def __init__(self, output_dir: str = "data"):
        """
        Initialize data handler with output directory and load existing IDs
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
        self._processed_ids = set()  # Track processed tweet IDs
        self._initialize_files()

    def _ensure_output_dir(self) -> None:
        """Create output directory and subdirectories"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _initialize_files(self) -> None:
        """Initialize files and load processed IDs"""
        self.tweet_file = os.path.join(self.output_dir, "tweets.json")

        # Create files if they don't exist
        if not os.path.exists(self.tweet_file):
            self._safe_write(self.tweet_file, [])

        # Load processed IDs
        existing_data = self._safe_read(self.tweet_file)
        self._processed_ids = {tweet.get('tweet_id') for tweet in existing_data
                               if tweet.get('tweet_id')}

    def _safe_read(self, filepath: str) -> List[Dict]:
        """Safely read JSON file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error reading {filepath}: {e}. Starting fresh.")
        return []

    def _safe_write(self, filepath: str, data: List[Dict]) -> bool:
        """
        Safely write data to file using atomic operation
        Returns True if successful, False otherwise
        """
        temp_file = f"{filepath}.tmp"
        try:
            # Write to temporary file first
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            # Atomic replace
            os.replace(temp_file, filepath)
            return True
        except Exception as e:
            print(f"Error writing to {filepath}: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False

    def save_tweet(self, tweet_data: Dict) -> bool:
        """
        Save a single tweet if it's not a duplicate
        Returns True if saved, False if duplicate or error
        """
        tweet_id = tweet_data.get('tweet_id')
        if not tweet_id or tweet_id in self._processed_ids:
            return False

        existing_data = self._safe_read(self.tweet_file)
        tweet_data['crawled_at'] = datetime.now().isoformat()
        existing_data.append(tweet_data)

        if self._safe_write(self.tweet_file, existing_data):
            self._processed_ids.add(tweet_id)
            return True
        return False

    def update_tweet_comments(self, tweet_id: str, comments: List[Dict]) -> bool:
        """
        Update existing tweet with comments
        Returns True if updated, False if tweet not found or error
        """
        if not tweet_id or tweet_id not in self._processed_ids:
            return False

        existing_data = self._safe_read(self.tweet_file)
        updated = False

        for tweet in existing_data:
            if tweet.get('tweet_id') == tweet_id:
                tweet['comments'] = comments
                tweet['updated_at'] = datetime.now().isoformat()
                updated = True
                break

        if updated:
            return self._safe_write(self.tweet_file, existing_data)
        return False

    def get_tweet(self, tweet_id: str) -> Optional[Dict]:
        """Get single tweet by ID"""
        existing_data = self._safe_read(self.tweet_file)
        for tweet in existing_data:
            if tweet.get('tweet_id') == tweet_id:
                return tweet
        return None

    def get_all_tweets(self) -> List[Dict]:
        """Get all stored tweets"""
        return self._safe_read(self.tweet_file)

    def get_tweet_count(self) -> int:
        """Get total number of stored tweets"""
        return len(self._processed_ids)

    def clear_all_data(self) -> None:
        """Clear all stored data"""
        if os.path.exists(self.tweet_file):
            os.remove(self.tweet_file)
        self._processed_ids.clear()
        self._initialize_files()