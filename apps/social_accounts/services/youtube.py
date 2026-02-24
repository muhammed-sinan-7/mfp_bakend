import requests
import urllib.parse
import secrets
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import redirect

from apps.organizations.mixins import OrganizationContextMixin
from apps.social_accounts.models import SocialAccount, PublishingTarget, SocialProvider


class YouTubeOAuthService:

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    YT_API_BASE = "https://www.googleapis.com/youtube/v3"

    STATE_TTL = 600  

    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly",
    ]

    
    @staticmethod
    def generate_authorization_url(organization_id):

        state = secrets.token_urlsafe(32)

        cache.set(
            f"youtube_oauth_state:{state}",
            str(organization_id),
            timeout=YouTubeOAuthService.STATE_TTL,
        )

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(YouTubeOAuthService.SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }

        return YouTubeOAuthService.AUTH_URL + "?" + urllib.parse.urlencode(params)

  
    @staticmethod
    def exchange_code(code):

        response = requests.post(
            YouTubeOAuthService.TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            },
            timeout=10,
        )

        if response.status_code != 200:
            raise Exception("YouTube token exchange failed")

        return response.json()

    @staticmethod
    def refresh_access_token(refresh_token):

        response = requests.post(
            YouTubeOAuthService.TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        timeout=10,
    )

        if response.status_code != 200:
            raise Exception("YouTube token refresh failed")

        return response.json()

    @staticmethod
    def fetch_channel(access_token):

        response = requests.get(
            f"{YouTubeOAuthService.YT_API_BASE}/channels",
            params={
                "part": "snippet",
                "mine": "true",
            },
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            timeout=10,
        )

        if response.status_code != 200:
            raise Exception("Failed to fetch YouTube channel")

        return response.json()

  
    @staticmethod
    def validate_state(state):

        org_id = cache.get(f"youtube_oauth_state:{state}")

        if not org_id:
            raise Exception("Invalid or expired YouTube OAuth state")

        cache.delete(f"youtube_oauth_state:{state}")

        return org_id
    

class YouTubeConnectView(OrganizationContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        if not request.organization:
            return Response({"error": "Organization not found"}, status=400)

        auth_url = YouTubeOAuthService.generate_authorization_url(
            request.organization.id
        )

        return Response({"authorization_url": auth_url})
    
class YouTubeCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        code = request.GET.get("code")
        state = request.GET.get("state")

        if not code or not state:
            return Response({"error": "Missing code or state"}, status=400)

        org_id = YouTubeOAuthService.validate_state(state)

        token_data = YouTubeOAuthService.exchange_code(code)

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)

        channel_data = YouTubeOAuthService.fetch_channel(access_token)

        if not channel_data.get("items"):
            return Response({"error": "No YouTube channel found"}, status=400)

        channel = channel_data["items"][0]

        external_id = channel["id"]
        channel_name = channel["snippet"]["title"]

        social_account, _ = SocialAccount.objects.update_or_create(
            organization_id=org_id,
            provider=SocialProvider.YOUTUBE,
            external_id=external_id,
            defaults={
                "account_name": channel_name,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_expires_at": timezone.now() + timedelta(seconds=expires_in),
                "is_active": True,
            },
        )

        PublishingTarget.objects.update_or_create(
            social_account=social_account,
            provider=SocialProvider.YOUTUBE,
            resource_id=external_id,
            defaults={
                "display_name": channel_name,
                "metadata": channel,
                "is_active": True,
            },
        )

        return redirect(settings.FRONTEND_SUCCESS_URL)