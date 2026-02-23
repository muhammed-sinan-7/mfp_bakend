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


class MetaConnectView(APIView):
    permission_classes = [AllowAny]

    def generate_state(self, user_id, org_id):
        payload = {
            "user_id": user_id,
            "org_id": org_id,
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
        org_id = request.query_params.get("org_id")

        if not org_id:
            return Response({"error": "org_id required"}, status=400)

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

        return redirect(auth_url)




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

       
        pages_data = service.fetch_pages(long_token)
     

        if "data" not in pages_data:
            return Response(pages_data, status=400)

        pages = pages_data["data"]

        

        from django.utils import timezone
        from datetime import timedelta
        from apps.social_accounts.models import SocialAccount, SocialProvider

        expires_in = long_token_data.get("expires_in", 60 * 24 * 60 * 60)
        expires_at = timezone.now() + timedelta(seconds=expires_in)

        for page in pages:

            page_id = page["id"]
            page_name = page["name"]
            page_token = page["access_token"]

            ig_data = service.fetch_instagram_business(page_id, page_token)

            instagram_business = None
            if "instagram_business_account" in ig_data:
                instagram_business = ig_data["instagram_business_account"]

            SocialAccount.objects.update_or_create(
                organization_id=payload["org_id"],
                provider=SocialProvider.META,
                external_id=page_id,
                defaults={
                    "account_name": page_name,
                    "access_token": page_token,  # auto encrypted
                    "token_expires_at": expires_at,
                    "scopes": service.SCOPES,
                    "metadata": {
                        "instagram_business_id": instagram_business["id"]
                        if instagram_business else None
                    },
                    "is_active": True,
                }
            )


        return redirect(settings.FRONTEND_SUCCESS_URL)