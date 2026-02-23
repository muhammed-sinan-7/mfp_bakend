# mfp_backend/apps/social/tasks.py

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.social_accounts.models import SocialAccount


@shared_task
def dispatch_expiring_meta_refresh_tasks():
    """
    Runs every 12 hours.
    Finds META accounts expiring within 5 days.
    Dispatches individual refresh tasks.
    """

    threshold = timezone.now() + timedelta(days=5)

    accounts = SocialAccount.objects.filter(
        provider="META",
        is_active=True,
        token_expires_at__lte=threshold
    ).values_list("id", flat=True)

    for account_id in accounts:
        refresh_meta_account_task.delay(account_id)


@shared_task(bind=True, max_retries=3)
def refresh_meta_account_task(self, account_id: int):
    """
    Refresh a single Meta account.
    Each account runs independently.
    """

    from apps.social_accounts.services.meta_token_service import MetaTokenService

    try:
        MetaTokenService.refresh_account(account_id)

    except Exception as exc:
        # Exponential backoff retry
        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** self.request.retries)
        )