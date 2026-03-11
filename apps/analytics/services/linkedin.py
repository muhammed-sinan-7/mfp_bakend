# apps/analytics/services/linkedin.py

import requests
from .base import empty_metrics


def fetch(post_platform):

    account = post_platform.publishing_target.social_account
    access_token = account.access_token

    # external_post_id stored during publishing
    post_id = post_platform.external_post_id

    url = f"https://api.linkedin.com/v2/socialActions/{post_id}"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        return None

    data = res.json()

    metrics = empty_metrics()

    metrics["likes"] = data.get("likesSummary", {}).get("totalLikes", 0)
    metrics["comments"] = data.get("commentsSummary", {}).get("totalFirstLevelComments", 0)

    return metrics