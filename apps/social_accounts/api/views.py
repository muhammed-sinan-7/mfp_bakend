import requests
import base64
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from ..services.meta import MetaOAuthService
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.organizations.mixins import OrganizationContextMixin
from apps.social_accounts.services.linkedin import LinkedInOAuthService
from apps.social_accounts.models import SocialAccount,SocialProvider
from apps.social_accounts.services.meta_sync_service import MetaSyncService
from ..tasks import sync_meta_pages_task
from apps.social_accounts.services.linkedin import LinkedInService

class MetaConnectView(OrganizationContextMixin,APIView):
    permission_classes = [AllowAny]

    def generate_state(self, user_id, org_id):
        payload = {
            "user_id": str(user_id),
            "org_id": str(org_id),
            "timestamp": int(time.time())
        }

        payload_bytes = json.dumps(payload).encode()
        payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode()

        signature = hmac.new(
            settings.META_STATE_SECRET.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"{payload_b64}.{signature}"

    def get(self, request):
        organization = request.organization

        if not organization:
            return Response(
                {"error": "Organization not found"},
                status=400
            )

        org_id = organization.id

        state = self.generate_state(request.user.id, org_id)

        params = {
            "client_id": settings.META_APP_ID,
            "redirect_uri": settings.META_REDIRECT_URI,
            "state": state,
            "scope": ",".join([
                "pages_show_list",
                "pages_read_engagement",
                "instagram_basic",
                "instagram_content_publish"
            ]),
            "response_type": "code"
        }

        auth_url = (
            "https://www.facebook.com/v18.0/dialog/oauth?"
            + urlencode(params)
        )

        return Response({"authorization_url": auth_url})




class MetaCallbackView(APIView):
    permission_classes = [AllowAny]

    def verify_state(self, state):
        try:
            payload_b64, signature = state.split(".")

            expected_signature = hmac.new(
                settings.META_STATE_SECRET.encode(),
                payload_b64.encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                return None

            payload_json = base64.urlsafe_b64decode(payload_b64.encode())
            payload = json.loads(payload_json)

            # expire after 10 minutes
            if time.time() - payload["timestamp"] > 600:
                return None

            return payload

        except Exception:
            return None

    def get(self, request):

        code = request.GET.get("code")
        state = request.GET.get("state")

        if not code or not state:
            return Response({"error": "Missing code or state"}, status=400)

        payload = self.verify_state(state)
        if not payload:
            return Response({"error": "Invalid state"}, status=400)

        service = MetaOAuthService()

      
        token_data = service.exchange_code(code)
        if "access_token" not in token_data:
            return Response(token_data, status=400)

        short_token = token_data["access_token"]

        
        long_token_data = service.get_long_lived_token(short_token)
        if "access_token" not in long_token_data:
            return Response(long_token_data, status=400)

        long_token = long_token_data["access_token"]

    
        from django.utils import timezone
        from datetime import timedelta

        expires_in = long_token_data.get("expires_in", 60 * 24 * 60 * 60)
        expires_at = timezone.now() + timedelta(seconds=expires_in)

        
        profile = service.fetch_user_profile(long_token)

        meta_user_id = profile["id"]
        meta_user_name = profile.get("name", "Meta Account")

        
        social_account, _ = SocialAccount.objects.update_or_create(
            organization_id=payload["org_id"],
            provider=SocialProvider.META,
            external_id=meta_user_id,
            defaults={
                "account_name": meta_user_name,
                "access_token": long_token,
                "token_expires_at": expires_at,
                "scopes": service.SCOPES,
                "is_active": True,
            }
        )

        
        sync_meta_pages_task.delay(social_account.id)

    
        return redirect(f"{settings.FRONTEND_SUCCESS_URL}/accounts")
    
    
class MetaPageSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        social_account = SocialAccount.objects.get(
            organization=request.user.organization,
            provider=SocialProvider.META,
            is_active=True,
        )

        sync_meta_pages_task.delay(social_account.id)
        return Response({"message": "Sync started"})


class LinkedInConnectView(OrganizationContextMixin,APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        
        organization = request.organization

        if not organization:
            return Response(
                {"error": "Organization not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        auth_url = LinkedInOAuthService.generate_authorization_url(
            organization_id=organization.id
        )

        return Response({"authorization_url": auth_url})
    
    
class LinkedInCallbackView(OrganizationContextMixin,APIView):

    def get(self, request):
        
        code = request.GET.get("code")
        state = request.GET.get("state")

        if not code or not state:
            return Response(
                {"error": "Missing code or state"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            
            org_id = LinkedInOAuthService.validate_state(state)

            
            token_data = LinkedInOAuthService.exchange_code(code)

           
            profile_data = LinkedInOAuthService.fetch_profile(
                token_data.get("access_token")
            )

            
            LinkedInOAuthService.save_account(
                org_id=org_id,
                token_data=token_data,
                profile_data=profile_data
            )
           
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return redirect(f"{settings.FRONTEND_SUCCESS_URL}/accounts")
    

from .serializers import SocialAccountSerializer
class SocialAccountListView(OrganizationContextMixin,APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = request.organization

        accounts = SocialAccount.objects.filter(
            organization=organization
        )

        serializer = SocialAccountSerializer(accounts, many=True)

        return Response(serializer.data)