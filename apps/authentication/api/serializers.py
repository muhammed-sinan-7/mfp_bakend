from rest_framework import serializers
from apps.authentication.models import OTPToken,User
from django.contrib.auth import get_user_model
from apps.authentication.services import user_service
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
User = get_user_model()

class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    
class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6,min_length=6)
    


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email","password",]

    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value

    
    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number is already registered.")
        return value

    
    def create(self, validated_data):
       
        user = user_service.register_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user
    

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_active:
            raise serializers.ValidationError("Account not activated")


        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }