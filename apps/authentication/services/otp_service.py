# apps/authentication/services/otp_service.py

import secrets
from datetime import timedelta

import bcrypt
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.authentication.exceptions import (
    OTPCooldownException,
    OTPInvalidException,
    OTPLockedException,
)
from apps.authentication.models import OTPToken

from ..tasks import send_otp_email_task


def generate_otp():
    return str(secrets.randbelow(900000) + 100000)


@transaction.atomic
def create_otp(user, purpose):

    cache_key = f"otp_cooldown:{user.id}:{purpose}"

    if cache.get(cache_key):
        raise OTPCooldownException()

    cache.set(cache_key, True, timeout=60)

    OTPToken.objects.filter(
        user=user,
        purpose=purpose,
        is_used=False,
    ).update(is_used=True)

    otp = generate_otp()

    otp_hash = bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()
    expires_at = timezone.now() + timedelta(minutes=5)

    OTPToken.objects.create(
        user=user,
        otp_hash=otp_hash,
        purpose=purpose,
        expires_at=expires_at,
    )

    transaction.on_commit(lambda: send_otp_email_task.delay(user.email, otp))

    return True


@transaction.atomic
def verify_otp(user, purpose, otp_input):
    otp_obj = (
        OTPToken.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False,
        )
        .order_by("-created_at")
        .first()
    )

    if not otp_obj or otp_obj.expires_at < timezone.now():
        raise OTPInvalidException()

    if otp_obj.attempt_count >= 5:
        raise OTPLockedException()

    if not bcrypt.checkpw(otp_input.encode(), otp_obj.otp_hash.encode()):
        otp_obj.attempt_count += 1
        otp_obj.save(update_fields=["attempt_count"])

        remaining = 5 - otp_obj.attempt_count
        raise OTPInvalidException(f"{remaining}")

    otp_obj.is_used = True
    otp_obj.save(update_fields=["is_used"])

    return True
