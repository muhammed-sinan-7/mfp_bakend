from datetime import date, timedelta

from django.conf import settings
from django.db.models import Max, OuterRef, Subquery, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.mixins import OrganizationContextMixin
from apps.social_accounts.models import SocialProvider

from ..models import PostPlatformAnalytics, PostPlatformAnalyticsSnapshot

start_date = timezone.now() - timedelta(days=30)


class YouTubeOverviewView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization
        if org is None:
            return Response({"error": "Organization context missing"}, status=400)

        qs = PostPlatformAnalytics.objects.filter(
            post_platform__post__organization_id=org.id,
            post_platform__publishing_target__provider=SocialProvider.YOUTUBE,
        )

        data = qs.aggregate(
            views=Sum("views"),
            likes=Sum("likes"),
            comments=Sum("comments"),
            watch_time=Sum("watch_time"),
        )

        return Response(
            {
                "subscribers": 128492,
                "watch_time": data["watch_time"] or 0,
                "estimated_revenue": 12840,
            }
        )


class YouTubeGrowthChartView(OrganizationContextMixin, APIView):

    def get(self, request):
        org = request.organization
        if org is None:
            return Response({"error": "Organization context missing"}, status=400)

        start_date = timezone.now() - timedelta(days=30)

        qs = (
            PostPlatformAnalyticsSnapshot.objects.filter(
                post_platform__post__organization_id=org.id,
                post_platform__publishing_target__provider=SocialProvider.YOUTUBE,
                captured_at__gte=start_date,
            )
            .annotate(day=TruncDate("captured_at"))
            .order_by("day", "-captured_at")  # important
            .distinct("day")  # PostgreSQL DISTINCT ON
            .values("day", "views", "watch_time")
            .order_by("day")
        )

        data = [
            {
                "day": row["day"],
                "views": row["views"],
                "duration": row["watch_time"],
            }
            for row in qs
        ]

        return Response(data)


class YouTubeVideoAnalyticsView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization
        if org is None:
            return Response({"error": "Organization context missing"}, status=400)
        qs = PostPlatformAnalytics.objects.filter(
            post_platform__post__organization_id=org.id,
            post_platform__publishing_target__provider=SocialProvider.YOUTUBE,
        ).order_by("-id")[:20]

        data = []

        for v in qs:

            data.append(
                {
                    "video_id": v.post_platform.post.id,
                    "title": v.post_platform.caption
                    or f"YouTube Video {v.post_platform.id}",
                    "views": v.views,
                    "ctr": round((v.likes / v.views * 100) if v.views else 0, 2),
                    "comments": v.comments,
                    "status": "Trending" if v.views > 50000 else "Published",
                }
            )

        return Response(data)


class YouTubeTrafficSourcesView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization

        if org is None:
            return Response({"error": "Organization context missing"}, status=400)

        account = org.social_accounts.filter(provider=SocialProvider.YOUTUBE).first()

        if not account:
            return Response([])

        credentials = Credentials(
            token=account.access_token,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )

        yt_analytics = build("youtubeAnalytics", "v2", credentials=credentials)

        end = date.today()
        start = end - timedelta(days=30)

        report = (
            yt_analytics.reports()
            .query(
                ids="channel==MINE",
                startDate=start.isoformat(),
                endDate=end.isoformat(),
                metrics="views",
                dimensions="insightTrafficSourceType",
                sort="-views",
            )
            .execute()
        )

        rows = report.get("rows", [])

        TRAFFIC_LABELS = {
            "YT_SEARCH": "YouTube Search",
            "SUGGESTED_VIDEO": "Suggested Videos",
            "BROWSE": "Browse Features",
            "EXTERNAL": "External",
        }

        total = sum(r[1] for r in rows)

        data = []

        for src, views in rows:

            pct = round((views / total) * 100, 2) if total else 0

            data.append(
                {"label": TRAFFIC_LABELS.get(src, src), "value": pct, "views": views}
            )

        return Response(data)
