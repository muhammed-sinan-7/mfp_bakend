from rest_framework import serializers
from apps.posts.models import Post, PostPlatform
from django.utils import timezone
from rest_framework import serializers
from django.db import transaction
from rest_framework import serializers
from apps.posts.models import Post, PostPlatform, PostPlatformMedia
from apps.posts.models import Post, PostPlatform, PostPlatformMedia, MediaType
from apps.social_accounts.models import PublishingTarget
from rest_framework import serializers
from django.utils import timezone

from apps.posts.models import PostPlatform

class PostCreateSerializer(serializers.Serializer):

    caption = serializers.CharField(required=False, allow_blank=True)
    scheduled_time = serializers.DateTimeField()
    publishing_target_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )


    def validate(self, attrs):

        request = self.context["request"]
        org_id = request.organization.id

        targets = PublishingTarget.objects.filter(
            id__in=attrs["publishing_target_ids"],
            social_account__organization_id=org_id,
            is_active=True
        )

        if targets.count() != len(attrs["publishing_target_ids"]):
            raise serializers.ValidationError("Invalid publishing targets.")

        if attrs["scheduled_time"] < timezone.now():
            raise serializers.ValidationError("Cannot schedule in the past.")

        return attrs

    @transaction.atomic
    def create(self, validated_data):

        request = self.context["request"]
        organization = request.organization

        caption = validated_data.get("caption", "")
        scheduled_time = validated_data["scheduled_time"]
        target_ids = validated_data["publishing_target_ids"]

       
        post = Post.objects.create(
            organization=organization,
            created_by=request.user
        )

        targets = PublishingTarget.objects.filter(id__in=target_ids)

        for target in targets:

            platform = PostPlatform.objects.create(
                post=post,
                publishing_target=target,
                caption=caption,
                scheduled_time=scheduled_time
            )

            target_id_str = str(target.id)

            image_key = f"image_{target_id_str}"
            video_key = f"video_{target_id_str}"

            order = 0

            if image_key in request.FILES:
                PostPlatformMedia.objects.create(
                    post_platform=platform,
                    file=request.FILES[image_key],
                    media_type=MediaType.IMAGE,
                    order=order
                )
                order += 1

        
            if video_key in request.FILES:
                PostPlatformMedia.objects.create(
                    post_platform=platform,
                    file=request.FILES[video_key],
                    media_type=MediaType.VIDEO,
                    order=order
                )
                order += 1

        return post
    
    


class PlatformSummarySerializer(serializers.ModelSerializer):
    provider = serializers.CharField(
        source="publishing_target.provider"
    )

    class Meta:
        model = PostPlatform
        fields = [
            "id",
            "provider",
            "publish_status",
            "scheduled_time",
            "external_post_id",
            "caption"
        ]


class PostListSerializer(serializers.ModelSerializer):

    platforms = PlatformSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "created_at",
            "updated_at",
            "platforms",
            
            
        ]
        



class MediaSerializer(serializers.ModelSerializer):

    class Meta:
        model = PostPlatformMedia
        fields = [
            "id",
            "file",
            "media_type",
            "order",
        ]


class PlatformDetailSerializer(serializers.ModelSerializer):

    provider = serializers.CharField(
        source="publishing_target.provider"
    )

    media = MediaSerializer(many=True)

    class Meta:
        model = PostPlatform
        fields = [
            "id",
            "provider",
            "caption",
            "scheduled_time",
            "publish_status",
            "external_post_id",
            "failure_reason",
            "media",
        ]


class PostDetailSerializer(serializers.ModelSerializer):

    platforms = PlatformDetailSerializer(many=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "created_at",
            "updated_at",
            "platforms",
        ]
        



class PlatformUpdateSerializer(serializers.Serializer):

    id = serializers.UUIDField()
    caption = serializers.CharField(required=False)
    scheduled_time = serializers.DateTimeField(required=False)

    def validate(self, attrs):

        platform = PostPlatform.objects.get(id=attrs["id"])

        if platform.publish_status != "pending":
            raise serializers.ValidationError(
                "Cannot edit already processing/published posts."
            )

        if "scheduled_time" in attrs:
            if attrs["scheduled_time"] < timezone.now():
                raise serializers.ValidationError(
                    "Scheduled time must be in future."
                )

        return attrs
    