from urllib.parse import urlencode
from django.conf import settings


class MetaOAuthService:

    AUTH_BASE_URL = "https://www.facebook.com/v18.0/dialog/oauth"

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