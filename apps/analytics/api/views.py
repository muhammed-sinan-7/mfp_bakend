from django.db.models import Sum,Max
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.posts.models import Post
from ..models import PostPlatformAnalytics
from django.db.models.functions import TruncDate
from apps.organizations.mixins import OrganizationContextMixin
from apps.posts.models import PostPlatform
from .serializers import PostAnalyticsSerializer
from ..models import PostPlatformAnalyticsSnapshot
from django.db.models import F
from django.db.models.functions import TruncHour, TruncMinute


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
            views=Max("views"),
            likes=Sum("likes"),
            comments=Sum("comments"),
            shares=Sum("shares"),
        )

        total_engagement = (
            (data["likes"] or 0) + (data["comments"] or 0) + (data["shares"] or 0)
        )

        impressions = data["impressions"] or 0

        engagement_rate = total_engagement / impressions * 100 if impressions else 0

        return Response(
            {
                "total_impressions": data["impressions"] or 0,
                "total_views": data["views"] or 0,
                "total_likes": data["likes"] or 0,
                "total_comments": data["comments"] or 0,
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

        qs = PostPlatformAnalyticsSnapshot.objects.filter(
            post_platform__post__organization=org
        )

        if platform and platform != "overview":
            qs = qs.filter(
                post_platform__publishing_target__provider=platform
            )

        qs = (
            qs.annotate(time=TruncHour("captured_at"))
            .values(
                "time",
                "post_platform__publishing_target__provider"
            )
            .annotate(
                views=Max("views")
            )
            .order_by("time")
        )

        data = {}

        for row in qs:

            time = row["time"]
            provider = row["post_platform__publishing_target__provider"]
            if provider == "meta":
                provider = "instagram"
            views = row["views"] or 0

            if time not in data:
                data[time] = {"date": time}

            data[time][provider] = views

        return Response(list(data.values()))
    
    
    
class EngagementDistributionAPIView(APIView):

    def get(self, request):

        qs = (
            PostPlatformAnalyticsSnapshot.objects
            .values("platform")
            .annotate(
                engagement=Sum(
                    F("likes") + F("comments") + F("shares") + F("saves")
                )
            )
        )

        total = sum(item["engagement"] for item in qs)

        data = []

        for item in qs:
            percent = (item["engagement"] / total * 100) if total else 0

            data.append({
                "platform": item["platform"],
                "engagement": item["engagement"],
                "percentage": round(percent, 1)
            })

        return Response(data)
    
    
class RecentPostsAPIView(APIView):

    def get(self, request):

        latest_snapshots = (
            PostPlatformAnalyticsSnapshot.objects
            .order_by("post_platform", "-snapshot_time")
            .distinct("post_platform")
            .select_related("post_platform__post")
        )

        data = []

        for snap in latest_snapshots[:10]:

            engagement = (
                snap.likes +
                snap.comments +
                snap.shares +
                snap.saves
            )

            data.append({
                "post_id": snap.post_platform.post.id,
                "title": snap.post_platform.post.title,
                "platform": snap.platform,
                "impressions": snap.impressions,
                "engagement_rate": round(
                    (engagement / snap.impressions * 100) if snap.impressions else 0,
                    2
                ),
                "status": "High Growth" if engagement > 100 else "Standard"
            })

        return Response(data)