from rest_framework.generics import ListAPIView
from apps.social_accounts.models import PublishingTarget,SocialProvider
# from .serializers import PublishingTargetSerializer/

from rest_framework import serializers
from ..models import SocialAccount,PublishingTarget
from django.utils import timezone

class PublishingTargetSerializer(serializers.ModelSerializer):

    ui = serializers.SerializerMethodField()

    class Meta:
        model = PublishingTarget
        fields = [
            "id",
            "provider",
            "display_name",
            "ui",
        ]

    def get_ui(self, obj):
        return SocialProvider.ui_meta(obj.provider)


class SocialAccountSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    publishing_targets = PublishingTargetSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = SocialAccount
        fields = [
            "id",
            "provider",
            "account_name",
            "token_expires_at",
            "publishing_targets",
            "status",
        ]

    def get_status(self, obj):
        if not obj.is_active:
            return "disconnected"

        if obj.token_expires_at < timezone.now():
            return "disconnected"

        remaining = (obj.token_expires_at - timezone.now()).days

        if remaining <= 5:
            return "expiring"

        return "active"
    




from rest_framework import serializers
from apps.social_accounts.models import PublishingTarget


# class PublishingTargetSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PublishingTarget
#         fields = ["id", "provider", "display_name"]
