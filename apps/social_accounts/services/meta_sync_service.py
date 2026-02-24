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

            # ---- Save Facebook Page ----
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

            # ---- Fetch Instagram ----
            try:
                ig_data = oauth_service.fetch_instagram_account(
                    page_id=page_id,
                    page_token=page_token
                )

                if ig_data and ig_data.get("id"):

                    ig_id = ig_data["id"]

                    ig_profile = oauth_service.fetch_instagram_profile(
                        ig_id=ig_id,
                        page_token=page_token
                    )

                    ig_target, _ = PublishingTarget.objects.update_or_create(
                        social_account=social_account,
                        resource_id=ig_id,
                        defaults={
                            "provider": SocialProvider.INSTAGRAM,
                            "display_name": ig_profile.get("username"),
                            "metadata": ig_profile,
                        }
                    )

                    synced_targets.append(ig_target)

            except Exception as e:
                print("Instagram sync failed:", str(e))

        return synced_targets