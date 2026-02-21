from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from apps.authentication.api.serializers import (
    OTPRequestSerializer,
    OTPVerifySerializer,
    RegistrationSerializer,
    LoginSerializer,
)
from apps.authentication.services.otp_service import (
    create_otp,
    verify_otp,
    generate_otp,
)
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from apps.organizations.models import OrganizationMember
from rest_framework.permissions import IsAuthenticated
from apps.organizations.models import OrganizationMember


class OTPCreateBaseClass(APIView):

    purpose = None

    @swagger_auto_schema(request_body=OTPRequestSerializer)
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if self.purpose is None:
            return Response(
                {"error": "OTP purpose is not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        email = serializer.validated_data["email"]

        try:
            create_otp(email=email, purpose=self.purpose)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


class OTPVerifyBaseClass(APIView):
    purpose = None

    @swagger_auto_schema(request_body=OTPVerifySerializer)
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if self.purpose is None:
            return Response(
                {"error": "Purpose is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        try:
            user = verify_otp(email, self.purpose, otp)  
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)

        has_organization = OrganizationMember.objects.filter(user=user).exists()

        return Response(
            {
                "message": "OTP Verified Successfully",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "has_organization": has_organization,
            },
            status=status.HTTP_200_OK,
        )


class RequestEmailVerificationOTPView(OTPCreateBaseClass):

    purpose = "email_verification"


class VerifyEmailOTPView(OTPVerifyBaseClass):
    purpose = "email_verification"


class RegisterUserView(APIView):
    @swagger_auto_schema(request_body=RegistrationSerializer)
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.save()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "Registration successful. Please verify your email."},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = refresh_token(refresh_token)
            token.blacklist()
            return Response({"message": "Logged put succesfully"})
        except Exception:
            return Response({"error": "Invalid Token"}, status=400)


class TestProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "You are authenticated"})



class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            membership = OrganizationMember.objects.get(user=request.user)
        except OrganizationMember.DoesNotExist:
            return Response(
                {"error": "User does not belong to any organization."},
                status=403
            )

        return Response({
            "message": "Welcome to dashboard",
            "organization": membership.organization.name,
            "role": membership.role
        })