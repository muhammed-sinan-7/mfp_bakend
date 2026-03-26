import logging

from celery import shared_task

from apps.posts.models import PostPlatform, PublishStatus

from .services.registry import FETCHERS
from .services.sync import save_metrics

logger = logging.getLogger(__name__)


@shared_task
def sync_post_analytics():

    posts = PostPlatform.objects.filter(
        publish_status=PublishStatus.SUCCESS, external_post_id__isnull=False
    ).select_related("publishing_target", "publishing_target__social_account")

    for post in posts:

        provider = post.publishing_target.provider

        fetcher = FETCHERS.get(provider)

        if not fetcher:

            continue

        try:
            metrics = fetcher(post)

            if not metrics:

                continue

            save_metrics(post, metrics)

        except Exception as e:
            logger.error(f"Analytics sync error for {provider}: {e}")
