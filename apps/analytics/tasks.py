from celery import shared_task
from apps.posts.models import PostPlatform, PublishStatus
from .services.registry import FETCHERS
from .services.sync import save_metrics
import logging
logger = logging.getLogger(__name__)

@shared_task
def sync_post_analytics():

    posts = PostPlatform.objects.filter(
        publish_status=PublishStatus.SUCCESS,
        external_post_id__isnull=False
    ).select_related(
        "publishing_target",
        "publishing_target__social_account"
    )

    for post in posts:

        provider = post.publishing_target.provider

        logger.info(f"SYNC ANALYTICS → Provider: {provider}")
        logger.info(f"POST PLATFORM ID → {post.id}")

        fetcher = FETCHERS.get(provider)

        if not fetcher:
            logger.warning(f"No fetcher found for provider: {provider}")
            continue

        try:
            metrics = fetcher(post)

            if not metrics:
                logger.warning(f"No metrics returned for post {post.id}")
                continue

            save_metrics(post, metrics)

            logger.info(f"Saved analytics snapshot for {post.id}")

        except Exception as e:
            logger.error(f"Analytics sync error for {provider}: {e}")