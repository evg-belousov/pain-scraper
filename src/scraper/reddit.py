# src/scraper/reddit.py

import praw
import os
from datetime import datetime
from typing import List
from dataclasses import dataclass

from src.config import MIN_UPVOTES, MIN_COMMENTS, MAX_POST_AGE_DAYS


@dataclass
class RedditPost:
    id: str
    subreddit: str
    title: str
    body: str
    url: str
    author: str
    upvotes: int
    num_comments: int
    created_utc: datetime
    top_comments: List[str]


class RedditScraper:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent="PainScraper/1.0"
        )

    def search_subreddit(
        self,
        subreddit_name: str,
        keywords: List[str],
        limit: int = 100,
        time_filter: str = "month"  # hour, day, week, month, year, all
    ) -> List[RedditPost]:
        """Search subreddit for posts matching keywords."""

        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []

        for keyword in keywords:
            try:
                search_results = subreddit.search(
                    keyword,
                    limit=limit,
                    time_filter=time_filter,
                    sort="relevance"
                )

                for post in search_results:
                    if self._is_valid_post(post):
                        posts.append(self._convert_post(post))

            except Exception as e:
                print(f"Error searching {subreddit_name} for '{keyword}': {e}")
                continue

        # Remove duplicates by ID
        seen_ids = set()
        unique_posts = []
        for post in posts:
            if post.id not in seen_ids:
                seen_ids.add(post.id)
                unique_posts.append(post)

        return unique_posts

    def _is_valid_post(self, post) -> bool:
        """Check if post meets quality thresholds."""
        if post.score < MIN_UPVOTES:
            return False
        if post.num_comments < MIN_COMMENTS:
            return False
        if post.is_self is False:  # Skip link posts
            return False

        # Check age
        post_age = datetime.utcnow() - datetime.utcfromtimestamp(post.created_utc)
        if post_age.days > MAX_POST_AGE_DAYS:
            return False

        return True

    def _convert_post(self, post) -> RedditPost:
        """Convert PRAW post to our dataclass."""

        # Get top comments
        post.comments.replace_more(limit=0)
        top_comments = []
        for comment in post.comments[:5]:
            if hasattr(comment, 'body'):
                top_comments.append(comment.body[:500])

        return RedditPost(
            id=post.id,
            subreddit=post.subreddit.display_name,
            title=post.title,
            body=post.selftext[:5000],  # Limit body size
            url=f"https://reddit.com{post.permalink}",
            author=str(post.author) if post.author else "[deleted]",
            upvotes=post.score,
            num_comments=post.num_comments,
            created_utc=datetime.utcfromtimestamp(post.created_utc),
            top_comments=top_comments
        )

    def scrape_all_subreddits(
        self,
        subreddits: List[str],
        keywords: List[str],
        limit_per_subreddit: int = 50
    ) -> List[RedditPost]:
        """Scrape multiple subreddits."""

        all_posts = []

        for subreddit in subreddits:
            print(f"Scraping r/{subreddit}...")
            posts = self.search_subreddit(
                subreddit,
                keywords,
                limit=limit_per_subreddit
            )
            all_posts.extend(posts)
            print(f"  Found {len(posts)} posts")

        print(f"\nTotal: {len(all_posts)} posts")
        return all_posts
