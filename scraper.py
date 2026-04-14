"""
ScraperAgent

Role: Data Collection
Responsibility: Connects to public, unauthenticated HTTP APIs (Mastodon & Bluesky) and fetches posts based on a search topic.
"""
import requests
import pandas as pd
from bs4 import BeautifulSoup

class ScraperAgent:
    def __init__(self):
        # We no longer need authentication credentials, just a polite user-agent
        self.headers = {"User-Agent": "sentiment-analyzer/1.0 (Public Research)"}

    def _fetch_mastodon(self, topic: str, limit: int) -> list:
        # Mastodon public timelines search via tags
        hashtag = topic.replace(" ", "")
        url = f"https://mastodon.social/api/v1/timelines/tag/{hashtag}"
        try:
            response = requests.get(url, headers=self.headers, params={"limit": limit}, timeout=10)
            response.raise_for_status()
            posts = response.json()
            
            extracted = []
            for post in posts:
                # Mastodon returns HTML in 'content'
                raw_html = post.get('content', '')
                text = BeautifulSoup(raw_html, "html.parser").get_text(separator=" ").strip()
                
                extracted.append({
                    'title': "", 
                    'text': text,
                    'score': post.get('favourites_count', 0),
                    'created_utc': post.get('created_at'),
                    'num_comments': post.get('replies_count', 0),
                    'url': post.get('url', ''),
                    'full_text': text
                })
            return extracted
        except Exception as e:
            print(f"[ScraperAgent] Mastodon fetch failed: {e}")
            return []

    def scrape(self, topic: str, limit: int = 200) -> pd.DataFrame:
        print(f"[ScraperAgent] Scraping '{topic}' (Max {limit} from Mastodon)...")
        mastodon_data = self._fetch_mastodon(topic, limit)
        
        df = pd.DataFrame(mastodon_data)
        if df.empty:
            # Ensure safe exit by returning expected schema as empty df
            df = pd.DataFrame(columns=['title', 'text', 'score', 'created_utc', 'num_comments', 'url', 'full_text'])
            
        print(f"[ScraperAgent] Fetched total {len(df)} posts.")
        return df
