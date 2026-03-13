from celery import shared_task
from .services.rss_ingestion_service import RSSIntegrationService

@shared_task
def ingest_news():
    service = RSSIntegrationService()
    service.run()
    