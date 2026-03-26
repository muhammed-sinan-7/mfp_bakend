from apps.analytics.models import PostPlatformAnalytics, PostPlatformAnalyticsSnapshot


def save_metrics(post_platform, metrics):

    PostPlatformAnalyticsSnapshot.objects.create(
        post_platform=post_platform,
        impressions=metrics["impressions"],
        reach=metrics["reach"],
        views=metrics["views"],
        likes=metrics["likes"],
        comments=metrics["comments"],
        shares=metrics["shares"],
        saves=metrics["saves"],
        watch_time=metrics["watch_time"],
    )

    PostPlatformAnalytics.objects.update_or_create(
        post_platform=post_platform, defaults=metrics
    )
