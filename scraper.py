import requests
from bs4 import BeautifulSoup
import feedparser
import logging
from datetime import datetime, timedelta
import time as py_time

# Configure some common RSS feeds for Chhattisgarh
RSS_FEEDS = {
    "Patrika State": "https://www.patrika.com/chhattisgarh-news.xml",
    "Patrika Bastar/Jagdalpur": "https://www.patrika.com/jagdalpur-news.xml",
    "Patrika Surguja/Ambikapur": "https://www.patrika.com/ambikapur-news.xml",
    "Patrika Raipur": "https://www.patrika.com/raipur-news.xml",
    "IBC24 State": "https://www.ibc24.in/category/chhattisgarh/feed",
}

def fetch_feed_articles(max_per_feed=5, days_limit=2):
    """Fetches the latest articles from configured RSS feeds, filtered by date."""
    all_articles = []
    now = datetime.now()
    cutoff_date = now - timedelta(days=days_limit)
    
    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            count = 0
            for entry in feed.entries:
                if count >= max_per_feed:
                    break
                    
                # Parse the published date
                published_datetime = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_datetime = datetime.fromtimestamp(py_time.mktime(entry.published_parsed))
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_datetime = datetime.fromtimestamp(py_time.mktime(entry.updated_parsed))
                
                # Filter by date if available
                if published_datetime and published_datetime < cutoff_date:
                    continue
                
                all_articles.append({
                    "source": source_name,
                    "title": entry.title,
                    "url": entry.link,
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", ""),
                    "published_dt": published_datetime
                })
                count += 1
        except Exception as e:
            logging.error(f"Error fetching RSS {feed_url}: {e}")
    return all_articles

def fetch_article_text(url):
    """Fetches the full text of an article given its URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Generic paragraph extraction
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20])
        return text
    except Exception as e:
        logging.error(f"Error fetching article text {url}: {e}")
        return ""
