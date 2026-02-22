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
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import authenticate
from apps.audit.services import log_event
from apps.audit.models import AuditLog
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from apps.organizations.models import OrganizationMember
from rest_framework.permissions import IsAuthenticated
from apps.organizations.models import OrganizationMember


from apps.organizations.permissions import HasOrganization


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
        membership = OrganizationMember.objects.filter(user=user).first()
        organization = membership.organization if membership else None

        log_event(
            actor=user,
            organization=organization,
            action=AuditLog.ActionType.OTP_VERIFIED,
            request=request,
        )
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
        email = request.data.get("email")
        password = request.data.get("password")

        # Try to fetch user first (for lock check)
        user_model = (
            authenticate.__self__.get_user_model()
            if hasattr(authenticate, "__self__")
            else None
        )
        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            existing_user = User.objects.get(email=email)
        except User.DoesNotExist:
            existing_user = None

        if existing_user:
            existing_user.failed_login_attempts += 1

            if existing_user.failed_login_attempts >= 5:
                lock_minutes = min(
                    60, 5 * (2 ** (existing_user.failed_login_attempts - 5))
                )

                existing_user.account_locked_until = timezone.now() + timedelta(
                    minutes=lock_minutes
                )

                log_event(
                    actor=existing_user,
                    organization=None,
                    action=AuditLog.ActionType.ACCOUNT_LOCKED,
                    request=request,
                    metadata={"lock_minutes": lock_minutes},
                )

            existing_user.save(
                update_fields=["failed_login_attempts", "account_locked_until"]
            )

        user = authenticate(request, email=email, password=password)

        if not user:

            if existing_user:
                existing_user.failed_login_attempts += 1

                if existing_user.failed_login_attempts >= 5:
                    existing_user.account_locked_until = timezone.now() + timedelta(
                        minutes=15
                    )

                existing_user.save(
                    update_fields=["failed_login_attempts", "account_locked_until"]
                )

            log_event(
                actor=existing_user,
                organization=None,
                action=AuditLog.ActionType.LOGIN_FAILED,
                request=request,
                metadata={"email_attempted": email},
            )

            return Response({"error": "Invalid credentials"}, status=401)

        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.save(update_fields=["failed_login_attempts", "account_locked_until"])

        refresh = RefreshToken.for_user(user)

        membership = user.organization_memberships.filter(is_deleted=False).first()
        organization = membership.organization if membership else None

        log_event(
            actor=user,
            organization=organization,
            action=AuditLog.ActionType.LOGIN_SUCCESS,
            request=request,
        )

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "org_id": organization.id if organization else None,
                "org_name": organization.name if organization else None,
                "role": membership.role if membership else None,
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            log_event(
                actor=request.user,
                organization=(
                    request.organization if hasattr(request, "organization") else None
                ),
                action=AuditLog.ActionType.LOGOUT,
                request=request,
            )

            return Response({"message": "Logged out successfully"})

        except Exception:
            return Response({"error": "Invalid token"}, status=400)


class TestDashboardView(APIView):
    permission_classes = [IsAuthenticated, HasOrganization]

    def get(self, request):
        return Response({"message": "Dashboard acces granted"})


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = request.user.organization_memberships.filter(
            is_deleted=False
        ).first()

        if not membership:
            return Response(
                {"error": "User does not belong to any organization."},
                status=403,
            )

        return Response(
            {
                "message": "Welcome to dashboard",
                "organization": membership.organization.name,
                "role": membership.role,
            }
        )


class CustomTokenRefreshView(TokenRefreshView):

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            log_event(
                actor=request.user if request.user.is_authenticated else None,
                action=AuditLog.ActionType.TOKEN_REFRESH,
                request=request,
            )

        return response
