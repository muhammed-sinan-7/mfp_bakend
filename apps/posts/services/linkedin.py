import requests
from django.conf import settings
from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from .base import BasePublisher


class LinkedInPublisher(BasePublisher):

    BASE_URL = "https://api.linkedin.com/v2"

    def publish(self, post_platform):

        social_account = post_platform.publishing_target.social_account
        caption = post_platform.caption or ""

        if not social_account.access_token:
            raise Exception("Missing LinkedIn access token")

        if social_account.is_token_expired():
            raise Exception("LinkedIn token expired")

        access_token = social_account.access_token
        author_urn = f"urn:li:person:{post_platform.publishing_target.resource_id}"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        image = post_platform.media.filter(media_type="IMAGE").first()
        video = post_platform.media.filter(media_type="VIDEO").first()

        if video:
            media_urn = self._upload_video(
                video.file.path, access_token, social_account.external_id
            )
            share_media_category = "VIDEO"
        elif image:
            media_urn = self._upload_image(
                image.file.path, access_token, social_account.external_id
            )
            share_media_category = "IMAGE"
        else:
            media_urn = None
            share_media_category = "NONE"

        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": caption},
                    "shareMediaCategory": share_media_category,
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        if media_urn:
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "description": {"text": caption},
                    "media": media_urn,
                }
            ]

        response = requests.post(
            f"{self.BASE_URL}/ugcPosts", json=payload, headers=headers
        )

        if response.status_code not in [200, 201]:
            raise Exception(f"LinkedIn publish failed: {response.text}")

        return {"external_id": response.json().get("id")}

    def _upload_image(self, file_path, access_token, person_id):

        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        register_payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": f"urn:li:person:{person_id}",
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }

        register_res = requests.post(
            f"{self.BASE_URL}/assets?action=registerUpload",
            json=register_payload,
            headers=headers,
        )

        if register_res.status_code != 200:
            raise Exception(f"LinkedIn image register failed: {register_res.text}")

        data = register_res.json()

        upload_url = data["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset = data["value"]["asset"]

        with open(file_path, "rb") as f:
            upload_res = requests.put(upload_url, data=f)

        if upload_res.status_code not in [200, 201]:
            raise Exception("LinkedIn image upload failed")

        return asset

    def _upload_video(self, file_path, access_token, person_id):

        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        register_payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                "owner": f"urn:li:person:{person_id}",
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }

        register_res = requests.post(
            f"{self.BASE_URL}/assets?action=registerUpload",
            json=register_payload,
            headers=headers,
        )

        if register_res.status_code != 200:
            raise Exception(f"LinkedIn video register failed: {register_res.text}")

        data = register_res.json()

        upload_url = data["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset = data["value"]["asset"]

        with open(file_path, "rb") as f:
            upload_res = requests.put(upload_url, data=f)

        if upload_res.status_code not in [200, 201]:
            raise Exception("LinkedIn video upload failed")

        return asset
