from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import Post, PostPlatform, PostStatus, PublishStatus
from .services import get_publisher

BATCH_SIZE = 50


@shared_task(bind=True, max_retries=3)
def publish_platform(self, platform_id):

    try:
        with transaction.atomic():
            platform = (
                PostPlatform.objects.select_for_update()
                .select_related(
                    "publishing_target",
                    "publishing_target__social_account",
                    "post",
                )
                .get(id=platform_id)
            )

            
            if platform.external_post_id:
                return

            platform.publish_status = PublishStatus.PROCESSING
            platform.last_attempt_at = timezone.now()
            platform.save(update_fields=["publish_status", "last_attempt_at"])

        account = platform.publishing_target.social_account

        if account.is_token_expired():
            raise Exception("Access token expired")
        
        publisher = get_publisher(platform.publishing_target.provider)
        result = publisher.publish(platform)

        with transaction.atomic():
            platform = PostPlatform.objects.select_for_update().get(id=platform_id)
            platform.external_post_id = result.get("external_id")
            platform.publish_status = PublishStatus.SUCCESS
            platform.save(update_fields=["external_post_id", "publish_status"])

    except Exception as e:

        with transaction.atomic():
            platform = PostPlatform.objects.select_for_update().get(id=platform_id)

            platform.retry_count += 1
            platform.failure_reason = str(e)

            if platform.retry_count >= 3:
                platform.publish_status = PublishStatus.FAILED
            else:
                platform.publish_status = PublishStatus.PENDING

            platform.save(
                update_fields=[
                    "publish_status",
                    "retry_count",
                    "failure_reason",
                ]
            )

        raise self.retry(countdown=60 * (2**self.request.retries))


@shared_task
def dispatch_scheduled_platforms():
    now = timezone.now()

    with transaction.atomic():
        platforms = (
            PostPlatform.objects
            .select_for_update(skip_locked=True)
            .filter(
                publish_status=PublishStatus.PENDING,
                scheduled_time__lte=now,
                post__is_deleted=False,
            )
            .order_by("scheduled_time")[:50]
        )

        platform_ids = list(platforms.values_list("id", flat=True))

        
        PostPlatform.objects.filter(id__in=platform_ids).update(
            publish_status=PublishStatus.PROCESSING
        )

    for pid in platform_ids:
        publish_platform.delay(str(pid))
        
@shared_task
def purge_recycle_bin():

    threshold = timezone.now() - timedelta(days=2)

    posts = Post.objects.filter(
        is_deleted=True,
        deleted_at__lt=threshold
    )

    count = posts.count()

    posts.delete()

    return f"{count} posts permanently deleted"