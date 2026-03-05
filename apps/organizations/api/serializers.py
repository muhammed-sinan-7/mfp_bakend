from rest_framework import serializers
from apps.organizations.models import Organization
from apps.industries.models import Industry
from django.utils.text import slugify

class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["name", "industry", "tagline"]

    def create(self, validated_data):
        name = validated_data["name"]

        
        base_slug = slugify(name)
        slug = base_slug

        
        counter = 1
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        validated_data["slug"] = slug

        return super().create(validated_data)

    def validate_name(self, value):
        if Organization.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Organization name already exists")
        return value