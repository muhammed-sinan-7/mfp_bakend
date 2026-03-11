import requests
from .base import empty_metrics


def fetch(post_platform):

    access_token = post_platform.publishing_target.social_account.access_token
    media_id = post_platform.external_post_id

    metrics = empty_metrics()

   

    media_res = requests.get(
        f"https://graph.facebook.com/v19.0/{media_id}",
        params={
            "fields": "media_type,like_count,comments_count",
            "access_token": access_token
        }
    )

    if media_res.status_code != 200:
        print("INSTAGRAM MEDIA ERROR:", media_res.json())
        return metrics

    media = media_res.json()

    media_type = media.get("media_type")

    metrics["likes"] = media.get("like_count", 0)
    metrics["comments"] = media.get("comments_count", 0)



    insight_metric = "reach"

    if media_type == "REEL":
        insight_metric = "plays"

    elif media_type == "VIDEO":
        insight_metric = "video_views"

    elif media_type in ["IMAGE", "CAROUSEL_ALBUM"]:
        insight_metric = "reach"

  

    insights_res = requests.get(
        f"https://graph.facebook.com/v19.0/{media_id}/insights",
        params={
            "metric": insight_metric,
            "access_token": access_token
        }
    )

    if insights_res.status_code == 200:

        data = insights_res.json().get("data", [])

        if data and data[0].get("values"):

            value = data[0]["values"][0].get("value", 0)

            metrics["views"] = value
            metrics["reach"] = value

    else:
        print("INSTAGRAM INSIGHTS ERROR:", insights_res.json())

    return metrics