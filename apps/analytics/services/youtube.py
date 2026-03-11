
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from django.conf import settings
from .base import empty_metrics


def fetch(post_platform):

    account = post_platform.publishing_target.social_account

    credentials = Credentials(
        token=account.access_token,
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )

    youtube = build("youtube", "v3", credentials=credentials)

    res = youtube.videos().list(
        part="statistics",
        id=post_platform.external_post_id
    ).execute()

    items = res.get("items")

    if not items:
        return None

    stats = items[0]["statistics"]

    metrics = empty_metrics()

    metrics["views"] = int(stats.get("viewCount", 0))
    metrics["likes"] = int(stats.get("likeCount", 0))
    metrics["comments"] = int(stats.get("commentCount", 0))

    return metrics