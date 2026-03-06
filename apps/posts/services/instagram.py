import requests
from django.conf import settings
from .base import BasePublisher
from apps.social_accounts.models import MetaPage
from urllib.parse import urljoin


class InstagramPublisher(BasePublisher):

    BASE_URL = "https://graph.facebook.com/v18.0"

    def publish(self, post_platform):
        

        post = post_platform.post
        publishing_target = post_platform.publishing_target

        
        media = post_platform.media.all().filter(media_type="IMAGE").first()

        if not media:
            raise Exception("Instagram requires an image")

        ig_user_id = publishing_target.resource_id

        
        meta_page = MetaPage.objects.filter(
            social_account=publishing_target.social_account,
            instagram_business_id=ig_user_id
        ).first()

        if not meta_page:
            raise Exception("MetaPage not linked to Instagram account")

        access_token = meta_page.page_access_token

        
        image_url = urljoin(settings.BASE_URL, media.file.url)
        
        create_url = f"{self.BASE_URL}/{ig_user_id}/media"

        create_payload = {
            "image_url": image_url,
            "caption": post_platform.caption or "",
            "access_token": access_token,
        }

        create_response = requests.post(create_url, data=create_payload,timeout=30)
        
        if create_response.status_code != 200:
            raise Exception(f"IG container failed: {create_response.text}")

        container_id = create_response.json()["id"]

        
        publish_url = f"{self.BASE_URL}/{ig_user_id}/media_publish"

        publish_payload = {
            "creation_id": container_id,
            "access_token": access_token,
        }

        publish_response = requests.post(publish_url, data=publish_payload)

        if publish_response.status_code != 200:
            raise Exception(f"Instagram publish failed: {publish_response.text}")

        return {
            "external_id": publish_response.json()["id"]
        }