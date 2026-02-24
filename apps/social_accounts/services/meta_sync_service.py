from apps.social_accounts.models import (
    MetaPage,
    PublishingTarget,
    SocialProvider,
)
from .meta import MetaOAuthService


class MetaSyncService:

    @staticmethod
    def sync_pages(social_account):
        oauth_service = MetaOAuthService()

        pages_data = oauth_service.fetch_pages(
            user_token=social_account.access_token
        )

        synced_targets = []

        for page in pages_data.get("data", []):

            page_id = page["id"]
            page_name = page["name"]
            page_token = page["access_token"]


            meta_page, _ = MetaPage.objects.update_or_create(
                social_account=social_account,
                page_id=page_id,
                defaults={
                    "name": page_name,
                    "page_access_token": page_token,
                    "metadata": page,
                }
            )

            
            publishing_target, _ = PublishingTarget.objects.update_or_create(
                social_account=social_account,
                resource_id=page_id,
                defaults={
                    "provider": SocialProvider.META,
                    "display_name": page_name,
                    "metadata": page,
                }
            )

            synced_targets.append(publishing_target)

        return synced_targets