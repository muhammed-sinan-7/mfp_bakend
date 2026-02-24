from rest_framework import serializers
from ..models import SocialAccount
from django.utils import timezone

class SocialAccountSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = SocialAccount
        fields = [
            "id",
            "provider",
            "account_name",
            "token_expires_at",
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