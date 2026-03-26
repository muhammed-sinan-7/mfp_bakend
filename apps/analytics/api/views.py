from django.db.models import F, Max, OuterRef, Subquery, Sum
from django.db.models.functions import TruncDate, TruncHour, TruncMinute
from django.utils.timezone import now, timedelta
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.news.selectors import get_industry_news
from apps.organizations.mixins import OrganizationContextMixin
from apps.posts.models import Post, PostPlatform
from apps.social_accounts.models import PublishingTarget

from ..models import PostPlatformAnalytics, PostPlatformAnalyticsSnapshot
from .serializers import PostAnalyticsSerializer


class AnalyticsListView(APIView):

    def get(self, request):

        analytics = PostPlatformAnalytics.objects.select_related("post_platform")

        serializer = PostAnalyticsSerializer(analytics, many=True)

        return Response(serializer.data)


class AnalyticsOverviewView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization
        platform = request.query_params.get("platform")

        analytics = PostPlatformAnalytics.objects.filter(
            post_platform__post__organization=org
        )

        if platform:
            analytics = analytics.filter(
                post_platform__publishing_target__provider=platform
            )

        data = analytics.aggregate(
            impressions=Sum("impressions"),
            views=Sum("views"),
            likes=Sum("likes"),
            comments=Sum("comments"),
            shares=Sum("shares"),
        )

        impressions = data["impressions"] or 0
        views = data["views"] or 0
        likes = data["likes"] or 0
        comments = data["comments"] or 0
        shares = data["shares"] or 0

        engagement = likes + comments + shares

        engagement_rate = (engagement / views * 100) if impressions else 0

        return Response(
            {
                "total_impressions": impressions,
                "total_views": views,
                "total_likes": likes,
                "total_comments": comments,
                "engagement_rate": round(engagement_rate, 2),
            }
        )


class TopPostsAnalyticsView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization

        posts = (
            PostPlatformAnalytics.objects.filter(post_platform__post__organization=org)
            .annotate(engagement=F("likes") + F("comments") + F("shares"))
            .order_by("-engagement")[:10]
        )

        data = []

        for p in posts:

            data.append(
                {
                    "post_id": p.post_platform.post_id,
                    "platform": p.post_platform.publishing_target.provider,
                    "likes": p.likes,
                    "comments": p.comments,
                    "shares": p.shares,
                    "views": p.views,
                }
            )

        return Response(data)


class PlatformAnalyticsView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization

        analytics = (
            PostPlatformAnalytics.objects.filter(post_platform__post__organization=org)
            .values("post_platform__publishing_target__provider")
            .annotate(likes=Sum("likes"), comments=Sum("comments"), views=Max("views"))
        )

        return Response(analytics)


class EngagementChartView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization
        platform = request.query_params.get("platform")

        snapshots = PostPlatformAnalyticsSnapshot.objects.filter(
            post_platform__post__organization=org
        ).annotate(hour=TruncHour("captured_at"))

        if platform and platform != "overview":
            snapshots = snapshots.filter(
                post_platform__publishing_target__provider=platform
            )

        # latest snapshot per post per hour
        latest_per_hour = snapshots.values("post_platform_id", "hour").annotate(
            latest_time=Max("captured_at")
        )

        qs = snapshots.filter(
            captured_at__in=[row["latest_time"] for row in latest_per_hour]
        )

        # aggregate views per hour
        qs = (
            qs.values("hour", "post_platform__publishing_target__provider")
            .annotate(views=Sum("views"))
            .order_by("hour")
        )

        data = {}

        for row in qs:

            time = row["hour"]
            provider = row["post_platform__publishing_target__provider"]

            if provider == "meta":
                provider = "instagram"

            views = row["views"] or 0

            if time not in data:
                data[time] = {"date": time, "instagram": 0, "youtube": 0, "linkedin": 0}

            data[time][provider] = views

        return Response(list(data.values()))


class EngagementDistributionAPIView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization

        qs = PostPlatformAnalyticsSnapshot.objects.filter(
            post_platform__post__organization=org
        )

        # latest snapshot per post
        latest_ids = (
            qs.order_by("post_platform", "-captured_at")
            .distinct("post_platform")
            .values_list("id", flat=True)
        )

        latest = PostPlatformAnalyticsSnapshot.objects.filter(id__in=latest_ids)

        platform_data = latest.values(
            "post_platform__publishing_target__provider"
        ).annotate(
            engagement=Sum(F("likes") + F("comments") + F("shares") + F("saves"))
        )

        total = sum(item["engagement"] or 0 for item in platform_data)

        data = []

        for item in platform_data:

            platform = item["post_platform__publishing_target__provider"]
            engagement = item["engagement"] or 0

            percent = (engagement / total * 100) if total else 0

            data.append(
                {
                    "platform": platform,
                    "engagement": engagement,
                    "percentage": round(percent, 1),
                }
            )

        return Response(data)


class RecentPostsAPIView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization

        qs = (
            PostPlatformAnalytics.objects.filter(post_platform__post__organization=org)
            .select_related(
                "post_platform",
                "post_platform__post",
                "post_platform__publishing_target",
            )
            .order_by("-created_at")[:10]
        )

        data = []

        for item in qs:

            engagement = item.likes + item.comments + item.shares + item.saves

            platform = item.post_platform.publishing_target.provider

            impressions = item.impressions or item.views

            engagement_rate = (engagement / impressions * 100) if impressions else 0

            data.append(
                {
                    "post_id": item.post_platform.post.id,
                    "title": item.post_platform.caption or "Post",
                    "platform": platform,
                    "impressions": impressions,
                    "engagement_rate": round(engagement_rate, 2),
                    "status": "High Growth" if engagement > 100 else "Standard",
                }
            )

        return Response(data)


class FullDashboardAPIView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization
        today = now()
        last_7_days = today - timedelta(days=7)

        # ------------------ STATS ------------------
        analytics = PostPlatformAnalytics.objects.filter(
            post_platform__post__organization=org, created_at__gte=last_7_days
        )

        stats = analytics.aggregate(
            reach=Sum("impressions"),
            likes=Sum("likes"),
            comments=Sum("comments"),
            shares=Sum("shares"),
        )

        reach = stats["reach"] or 0
        engagement = (
            (stats["likes"] or 0) + (stats["comments"] or 0) + (stats["shares"] or 0)
        )

        engagement_rate = (engagement / reach * 100) if reach else 0

        # ------------------ TOP POSTS ------------------
        top_posts_qs = (
            PostPlatformAnalytics.objects.filter(post_platform__post__organization=org)
            .annotate(engagement=F("likes") + F("comments") + F("shares"))
            .order_by("-engagement")[:5]
        )

        top_posts = []
        for p in top_posts_qs:
            top_posts.append(
                {
                    "title": p.post_platform.caption,
                    "platform": p.post_platform.publishing_target.provider,
                    "engagement": p.engagement,
                }
            )

        # ------------------ RECENT POSTS ------------------
        recent_qs = (
            PostPlatform.objects.filter(post__organization=org)
            .select_related("publishing_target")
            .order_by("-created_at")[:5]
        )

        recent_posts = []
        for p in recent_qs:
            recent_posts.append(
                {
                    "title": p.caption,
                    "platform": p.publishing_target.provider,
                    "status": p.publish_status,
                }
            )

        # ------------------ NEWS ------------------
        news = []
        if org.industry:
            articles = get_industry_news(org.industry_id, page=1, limit=5)
            for a in articles:
                news.append(
                    {
                        "title": a.title,
                        "url": a.url,
                    }
                )

        # ------------------ RESPONSE ------------------
        return Response(
            {
                "stats": {"reach": reach, "engagement_rate": round(engagement_rate, 2)},
                "top_posts": top_posts,
                "recent_posts": recent_posts,
                "news": news,
            }
        )
