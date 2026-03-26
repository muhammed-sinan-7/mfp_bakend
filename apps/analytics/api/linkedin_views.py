from django.db.models import Max, Sum
from django.db.models.functions import TruncDate
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.mixins import OrganizationContextMixin

from ..models import PostPlatformAnalytics, PostPlatformAnalyticsSnapshot


class LinkedInOverviewView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization

        qs = PostPlatformAnalytics.objects.filter(
            post_platform__post__organization=org,
            post_platform__publishing_target__provider="linkedin",
        )

        data = qs.aggregate(
            impressions=Sum("impressions"),
            views=Max("views"),
            likes=Sum("likes"),
            comments=Sum("comments"),
            shares=Sum("shares"),
        )

        return Response(
            {
                "connections": data["likes"] or 0,
                "unique_visitors": data["views"] or 0,
                "post_impressions": data["impressions"] or 0,
                "click_through_rate": 4.2,  # placeholder
            }
        )


class LinkedInGrowthChartView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization

        qs = (
            PostPlatformAnalyticsSnapshot.objects.filter(
                post_platform__post__organization=org,
                post_platform__publishing_target__provider="linkedin",
            )
            .annotate(day=TruncDate("captured_at"))
            .values("day")
            .annotate(impressions=Sum("impressions"), clicks=Sum("likes"))
            .order_by("day")
        )

        return Response(list(qs))


class LinkedInPostAnalyticsView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization

        qs = PostPlatformAnalytics.objects.filter(
            post_platform__post__organization=org,
            post_platform__publishing_target__provider="linkedin",
        ).order_by("-created_at")[:20]

        data = []

        for p in qs:

            data.append(
                {
                    "post_id": p.post_platform.post.id,
                    "title": p.post_platform.caption or "LinkedIn Post",
                    "type": "post",
                    "impressions": p.impressions,
                    "clicks": p.likes,
                    "ctr": round(
                        (p.likes / p.impressions * 100) if p.impressions else 0, 2
                    ),
                    "status": "High Engagement" if p.likes > 100 else "Normal",
                }
            )

        return Response(data)
