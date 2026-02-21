from rest_framework import serializers
from apps.organizations.models import Organization
from apps.industries.models import Industry


class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["name", "industry", "tagline"]

    def validate_name(self, value):
        if Organization.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Organization name already exists")
        return value