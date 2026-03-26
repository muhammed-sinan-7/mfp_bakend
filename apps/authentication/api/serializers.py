# serializers.py

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.authentication.services import auth_service

User = get_user_model()


class RegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def create(self, validated_data):
        return auth_service.register_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)
