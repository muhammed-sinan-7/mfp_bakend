import feedparser
import requests
from datetime import datetime, timezone
from django.utils import timezone as dj_timezone
from bs4 import BeautifulSoup
from newspaper import Article
from ..models import NewsArticle, NewsSource
from apps.ai.services.llm_service import AIService
import logging

logger = logging.getLogger(__name__)
class RSSIntegrationService:

    def extract_full_content(self, url):
        try:
            article = Article(url)
            article.download()
            article.parse()
            return article.text[:8000]  # prevent token explosion
        except:
            return ""

    def fetch_sources(self):
        return NewsSource.objects.filter(is_active=True)

    def parse_feed(self, source):
        return feedparser.parse(source.rss_url)

    def extract_og_image(self, url):
        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")

            tag = soup.find("meta", property="og:image")
            if tag:
                return tag.get("content")

        except Exception:
            return None

        return None
    

    def extract_articles(self, entry, source):

        published_time = getattr(entry, "published_parsed", None)

        image_url = None

     
        if hasattr(entry, "media_content"):
            media = entry.media_content
            if media and len(media) > 0:
                image_url = media[0].get("url")

        
        if not image_url and hasattr(entry, "media_thumbnail"):
            thumb = entry.media_thumbnail
            if thumb and len(thumb) > 0:
                image_url = thumb[0].get("url")

        
        if not image_url and hasattr(entry, "enclosures"):
            enclosure = entry.enclosures
            if enclosure and len(enclosure) > 0:
                image_url = enclosure[0].get("href")

        
        if not image_url and hasattr(entry, "content"):
            soup = BeautifulSoup(entry.content[0].value, "html.parser")
            img = soup.find("img")
            if img:
                image_url = img.get("src")

        
        if not image_url and hasattr(entry, "summary"):
            soup = BeautifulSoup(entry.summary, "html.parser")
            img = soup.find("img")
            if img:
                image_url = img.get("src")

        
        if not image_url:
            image_url = self.extract_og_image(getattr(entry, "link", ""))

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
    
    
    def generate_ai_summary(self, title, content):
        try:
            if not content:
                return ""

            ai = AIService()

            prompt = f"""
                You are a senior industry analyst.

                Summarize this article clearly and insightfully.

                Title: {title}

                Content:
                {content}

                RULES:
                - 6–10 lines
                - Explain what happened
                - Why it matters
                - Key insights
                - No fluff
                """

            result = ai.chat([{"role": "user", "content": prompt}])

            return result.get("response", "")

        except Exception:
            return ""

    def save_articles(self, data):

        if NewsArticle.objects.filter(url=data["url"]).exists():
            return None

        full_content = self.extract_full_content(data["url"])

        content_to_use = full_content if full_content else data["summary"]

        ai_summary = self.generate_ai_summary(
            data["title"],
            content_to_use
        )

        return NewsArticle.objects.create(
            **data,
            content=full_content,
            ai_summary=ai_summary
        )
        
    def run(self):
        sources = self.fetch_sources()

        total_processed = 0
        total_created = 0

        for source in sources:
            try:
                feed = self.parse_feed(source)

                if not hasattr(feed, "entries"):
                    continue

                for entry in feed.entries[:10]:  # limit per source
                    try:
                        article_data = self.extract_articles(entry, source)

                        if not article_data["url"]:
                            continue

                        total_processed += 1

                        created = self.save_articles(article_data)

                        if created:
                            total_created += 1

                    except Exception as e:
                        logger.warning(f"Entry failed: {e}", exc_info=True)

            except Exception as e:
                logger.error(f"Source failed: {source.rss_url}", exc_info=True)

        logger.info(
            f"News fetch completed | processed={total_processed}, created={total_created}"
        )