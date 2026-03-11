from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from apps.organizations.mixins import OrganizationContextMixin
from .serializers import PostCreateSerializer
from django.utils import timezone
from apps.posts.models import Post, PostPlatform
from apps.posts.api.serializers import PostListSerializer
from apps.posts.api.serializers import PostDetailSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from django.db import transaction
from apps.posts.api.serializers import PlatformUpdateSerializer
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from apps.audit.services import log_event
from apps.audit.models import AuditLog


class PostCreateAPIView(OrganizationContextMixin, APIView):

    def post(self, request):

        serializer = PostCreateSerializer(
            data=request.data, context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        post = serializer.save()

        log_event(
            actor=request.user,
            organization=request.organization,
            action=AuditLog.ActionType.POST_CREATED,
            request=request,
            target_model="Post",
            target_id=str(post.id),
        )

        return Response(
            {
                "post_id": str(post.id),
                # "status": post_platform.publish_status
            },
            status=status.HTTP_201_CREATED,
        )


class PostListView(OrganizationContextMixin, generics.ListAPIView):

    serializer_class = PostListSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = [
        "platforms__publishing_target__provider",
        "platforms__publish_status",
    ]

    search_fields = [
        "platforms__caption",
        "id",
    ]

    ordering_fields = [
        "created_at",
        "platforms__scheduled_time",
    ]

    def get_queryset(self):

        org = self.request.organization

        return (
            Post.objects.filter(organization=org, is_deleted=False)
            .prefetch_related("platforms", "platforms__publishing_target")
            .distinct()
            .order_by("-created_at")
        )


class PostUpdateView(OrganizationContextMixin, APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        post = Post.objects.get(
            id=pk, organization=request.organization, is_deleted=False
        )

        platforms_data = request.data.get("platforms", [])

        with transaction.atomic():

            for platform_data in platforms_data:

                serializer = PlatformUpdateSerializer(data=platform_data)
                serializer.is_valid(raise_exception=True)

                platform = PostPlatform.objects.get(
                    id=serializer.validated_data["id"], post=post
                )

                if "caption" in serializer.validated_data:
                    platform.caption = serializer.validated_data["caption"]

                if "scheduled_time" in serializer.validated_data:
                    platform.scheduled_time = serializer.validated_data[
                        "scheduled_time"
                    ]

                platform.save()
        log_event(
            actor=request.user,
            organization=request.organization,
            action=AuditLog.ActionType.POST_UPDATED,
            request=request,
            target_model="Post",
            target_id=str(post.id),
        )

        return Response({"message": "Post updated"})


class PostDetailView(OrganizationContextMixin, generics.RetrieveAPIView):

    serializer_class = PostDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Post.objects.filter(
            organization=self.request.organization, is_deleted=False
        ).prefetch_related(
            "platforms", "platforms__media", "platforms__publishing_target"
        )


class PostDeleteView(OrganizationContextMixin, APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        post = Post.objects.get(
            id=pk, organization=request.organization, is_deleted=False
        )

        post.is_deleted = True
        post.deleted_at = timezone.now()

        post.save(update_fields=["is_deleted", "deleted_at"])
        log_event(
            actor=request.user,
            organization=request.organization,
            action=AuditLog.ActionType.POST_DELETED,
            request=request,
            target_model="Post",
            target_id=str(post.id),
        )
        return Response({"message": "Post moved to recycle bin"})


class PostRestoreView(OrganizationContextMixin, APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        post = Post.objects.get(
            id=pk, organization=request.organization, is_deleted=True
        )

        post.is_deleted = False
        post.deleted_at = None

        post.save(update_fields=["is_deleted", "deleted_at"])
        log_event(
            actor=request.user,
            organization=request.organization,
            action=AuditLog.ActionType.POST_RESTORED,
            request=request,
            target_model="Post",
            target_id=str(post.id),
        )
        return Response({"message": "Post restored"})


class RecycleBinListView(OrganizationContextMixin, ListAPIView):

    serializer_class = PostListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return (
            Post.objects.filter(
                organization=self.request.organization,
                is_deleted=True
            )
            .select_related("created_by")
            .prefetch_related(
                "platforms",
                "platforms__publishing_target",
                "platforms__media"
            )
            .order_by("-deleted_at")
        )

class EmptyRecycleBinView(OrganizationContextMixin, APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request):

        deleted_posts = Post.objects.filter(
            organization=request.organization,
            is_deleted=True
        )

        count = deleted_posts.count()

        deleted_posts.delete()

        return Response({
            "message": "Recycle bin emptied",
            "deleted_count": count
        })
        
class PermanentDeletePostView(OrganizationContextMixin, APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        post = Post.objects.get(
            id=pk,
            organization=request.organization,
            is_deleted=True
        )

        post.delete()

        return Response({"message": "Post permanently deleted"})