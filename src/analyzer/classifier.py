# src/analyzer/classifier.py

import anthropic
import json
from typing import Optional, Dict, Callable

from src.scraper.reddit import RedditPost
from src.analyzer.prompts import CLASSIFICATION_PROMPT


class PainClassifier:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-20250514"

    def classify_post(self, post: RedditPost) -> Optional[Dict]:
        """Classify a single post."""

        comments_text = "\n---\n".join(post.top_comments[:3])

        prompt = CLASSIFICATION_PROMPT.format(
            subreddit=post.subreddit,
            title=post.title,
            body=post.body[:3000],
            comments=comments_text[:2000]
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text.strip()

            # Clean up potential markdown
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1]
                result_text = result_text.rsplit("```", 1)[0]

            result = json.loads(result_text)
            result["post_id"] = post.id
            result["post_url"] = post.url
            result["subreddit"] = post.subreddit
            result["upvotes"] = post.upvotes
            result["num_comments"] = post.num_comments
            result["post_created"] = post.created_utc.isoformat()

            return result

        except json.JSONDecodeError as e:
            print(f"JSON parse error for post {post.id}: {e}")
            return None
        except Exception as e:
            print(f"Error classifying post {post.id}: {e}")
            return None

    def classify_batch(
        self,
        posts: list[RedditPost],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> list[Dict]:
        """Classify multiple posts."""

        results = []

        for i, post in enumerate(posts):
            result = self.classify_post(post)

            if result and result.get("is_business_pain"):
                results.append(result)

            if progress_callback:
                progress_callback(i + 1, len(posts))

        return results
