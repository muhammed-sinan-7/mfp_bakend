from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from apps.organizations.mixins import OrganizationContextMixin
from .serializers import PostCreateSerializer
from django.utils import timezone
from apps.posts.models import Post,PostPlatform
from apps.posts.api.serializers import PostListSerializer
from apps.posts.api.serializers import PostDetailSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from django.db import transaction
from apps.posts.api.serializers import PlatformUpdateSerializer


class PostCreateAPIView(OrganizationContextMixin,APIView):

    def post(self, request):
        
        serializer = PostCreateSerializer(
            data=request.data,
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        post = serializer.save()

        return Response(
            {
                "post_id": str(post.id),
                # "status": post_platform.publish_status
            },
            status=status.HTTP_201_CREATED
        )
        
        
class PostListView(generics.ListAPIView):

    serializer_class = PostListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        org = self.request.organization

        return (
            Post.objects
            .filter(organization=org,is_deleted=False)
            .prefetch_related(
                "platforms",
                "platforms__publishing_target"
            )
            .order_by("-created_at")
        )
        
class PostUpdateView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        post = Post.objects.get(
            id=pk,
            organization=request.organization,
            is_deleted=False
        )

        platforms_data = request.data.get("platforms", [])

        with transaction.atomic():

            for platform_data in platforms_data:

                serializer = PlatformUpdateSerializer(data=platform_data)
                serializer.is_valid(raise_exception=True)

                platform = PostPlatform.objects.get(
                    id=serializer.validated_data["id"],
                    post=post
                )

                if "caption" in serializer.validated_data:
                    platform.caption = serializer.validated_data["caption"]

                if "scheduled_time" in serializer.validated_data:
                    platform.scheduled_time = serializer.validated_data["scheduled_time"]

                platform.save()

        return Response({"message": "Post updated"})
        
        
class PostDetailView(generics.RetrieveAPIView):

    serializer_class = PostDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return (
            Post.objects
            .filter(organization=self.request.organization,is_deleted=False)
            .prefetch_related(
                "platforms",
                "platforms__media",
                "platforms__publishing_target"
            )
        )
        
class PostDeleteView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        post = Post.objects.get(
            id=pk,
            organization=request.organization,
            is_deleted=False
        )

        post.is_deleted = True
        post.deleted_at = timezone.now()

        post.save(update_fields=["is_deleted", "deleted_at"])

        return Response({"message": "Post moved to recycle bin"})
    

class PostRestoreView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        post = Post.objects.get(
            id=pk,
            organization=request.organization,
            is_deleted=True
        )

        post.is_deleted = False
        post.deleted_at = None

        post.save(update_fields=["is_deleted", "deleted_at"])

        return Response({"message": "Post restored"})
    
class RecycleBinListView(ListAPIView):

    serializer_class = PostListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Post.objects.filter(
            organization=self.request.organization,
            is_deleted=True
        ).order_by("-deleted_at")