from datetime import timedelta

from django.db.models import F, Max, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.mixins import OrganizationContextMixin
from apps.social_accounts.models import SocialProvider

from ..models import PostPlatformAnalytics, PostPlatformAnalyticsSnapshot

start_date = timezone.now() - timedelta(days=30)


class InstagramOverviewView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization

        qs = PostPlatformAnalytics.objects.filter(
            post_platform__post__organization=org,
            post_platform__publishing_target__provider="instagram",
        )

        data = qs.aggregate(
            impressions=Sum("impressions"),
            views=Max("views"),
            likes=Sum("likes"),
            comments=Sum("comments"),
            saves=Sum("saves"),
        )

        return Response(
            {
                "accounts_reached": data["impressions"] or 0,
                "profile_visits": data["views"] or 0,
                "likes": data["likes"] or 0,
                "story_completion": data["saves"] or 0,
            }
        )


class InstagramGrowthChartView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization
        start_date = timezone.now() - timedelta(days=30)

        qs = (
            PostPlatformAnalyticsSnapshot.objects.filter(
                post_platform__post__organization_id=org.id,
                post_platform__publishing_target__provider=SocialProvider.INSTAGRAM,
                captured_at__gte=start_date,
            )
            .annotate(day=TruncDate("captured_at"))
            .order_by("day", "-captured_at")
            .distinct("day")
            .values("day", "likes", "comments")
            .order_by("day")
        )

        return Response(list(qs))


class InstagramTopPostsView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization

        qs = (
            PostPlatformAnalytics.objects.filter(
                post_platform__post__organization=org,
                post_platform__publishing_target__provider="instagram",
            )
            .annotate(engagement=F("likes") + F("comments") + F("shares"))
            .order_by("-engagement")[:5]
        )

        data = []

        for p in qs:

            data.append(
                {
                    "post_id": p.post_platform.post.id,
                    "title": p.post_platform.caption,
                    "likes": p.likes,
                    "comments": p.comments,
                    "engagement": p.engagement,
                }
            )

        return Response(data)


# class InstagramMediaGalleryView(OrganizationContextMixin, APIView):

#     def get(self, request):

#         org = request.organization

#         posts = PostPlatform.objects.filter(
#             post__organization=org,
#             publishing_target__provider="instagram"
#         ).order_by("-created_at")[:12]

#         data = []

#         for p in posts:
#             data.append({
#                 "post_id": p.post.id,
#                 "media": p.media_url,
#                 "caption": p.caption
#             })

#         return Response(data)


class InstagramPostPerformanceView(OrganizationContextMixin, APIView):

    def get(self, request):

        org = request.organization

        qs = PostPlatformAnalytics.objects.filter(
            post_platform__post__organization=org,
            post_platform__publishing_target__provider="instagram",
        ).order_by("-created_at")[:20]

        data = []

        for p in qs:

            engagement = p.likes + p.comments + p.shares

            data.append(
                {
                    "post_id": p.post_platform.post.id,
                    "title": p.post_platform.caption,
                    "engagement": engagement,
                    "reach": p.impressions,
                    "date": p.created_at,
                }
            )

        return Response(data)
