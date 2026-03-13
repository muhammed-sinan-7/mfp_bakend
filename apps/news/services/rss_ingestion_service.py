import feedparser
from datetime import datetime, timezone
from django.utils import timezone as dj_timezone
from bs4 import BeautifulSoup
from ..models import NewsArticle, NewsSource


class RSSIntegrationService:

    def fetch_sources(self):
        return NewsSource.objects.filter(is_active=True)

    def parse_feed(self, source):
        return feedparser.parse(source.rss_url)

    def extract_articles(self, entry, source):

        published_time = getattr(entry, "published_parsed", None)

        image_url = None

    
        if hasattr(entry, "media_content"):
            media = entry.media_content
            if media and len(media) > 0:
                image_url = media[0].get("url")

        
        elif hasattr(entry, "media_thumbnail"):
            thumb = entry.media_thumbnail
            if thumb and len(thumb) > 0:
                image_url = thumb[0].get("url")


        elif hasattr(entry, "enclosures"):
            enclosure = entry.enclosures
            if enclosure and len(enclosure) > 0:
                image_url = enclosure[0].get("href")
                
                
        if not image_url and hasattr(entry, "summary"):
            soup = BeautifulSoup(entry.summary, "html.parser")
            img = soup.find("img")
            if img:
                image_url = img.get("src")
            
            
        if published_time:
            published_time = datetime(*published_time[:6], tzinfo=timezone.utc)
        else:
            published_time = dj_timezone.now()

        data = {
            "title": getattr(entry, "title", ""),
            "summary": getattr(entry, "summary", ""),
            "url": getattr(entry, "link", ""),
            "image": image_url,
            "source": source,
            "industry": source.industry,
            "published_at": published_time,
        }

        return data

    def save_articles(self, data):

        exists = NewsArticle.objects.filter(url=data["url"]).exists()

        if exists:
            return None

        return NewsArticle.objects.create(**data)

    def run(self):

        sources = self.fetch_sources()

        for source in sources:

            feed = self.parse_feed(source)

            if not hasattr(feed, "entries"):
                continue

            for entry in feed.entries:

                article_data = self.extract_articles(entry, source)

                if not article_data["url"]:
                    continue

                self.save_articles(article_data)
