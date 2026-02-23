from urllib.parse import urlencode
from django.conf import settings
import requests

class MetaOAuthService:
    
    GRAPH_BASE = "https://graph.facebook.com/v18.0"
    AUTH_BASE_URL = "https://www.facebook.com/v18.0/dialog/oauth"

    def exchange_code(self, code: str):
        response = requests.get(
            f"{self.GRAPH_BASE}/oauth/access_token",
            params={
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "redirect_uri": settings.META_REDIRECT_URI,
                "code": code,
            },
        )
        return response.json()

    def get_long_lived_token(self, short_token: str):
        response = requests.get(
            f"{self.GRAPH_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "fb_exchange_token": short_token,
            },
        )
        return response.json()

    def fetch_pages(self, user_token: str):
        response = requests.get(
            f"{self.GRAPH_BASE}/me/accounts",
            params={"access_token": user_token},
        )
        return response.json()
    
    def fetch_instagram_business(self, page_id: str, page_token: str):
        response = requests.get(
            f"{self.GRAPH_BASE}/{page_id}",
            params={
                "fields": "instagram_business_account",
                "access_token": page_token,
            },
        )
        return response.json()


    SCOPES = [
        "pages_show_list",
        "pages_read_engagement",
        "pages_manage_posts",
        "instagram_basic",
        "instagram_content_publish",
    ]

    def get_authorization_url(self, state: str) -> str:
        params = {
            "client_id": settings.META_APP_ID,
            "redirect_uri": settings.META_REDIRECT_URI,
            "scope": ",".join(self.SCOPES),
            "response_type": "code",
            "state": state,
        }

        return f"{self.AUTH_BASE_URL}?{urlencode(params)}"