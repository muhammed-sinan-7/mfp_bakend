import secrets
import bcrypt
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.authentication.models import OTPToken
from ..tasks import send_otp_email_task

User = get_user_model()

def generate_otp():
    return str(secrets.randbelow(900000) + 100000)

def create_otp(email, purpose):
    try:
        
        user = User.objects.only('id').get(email=email)
    except User.DoesNotExist:
        raise Exception("User not found")

    
    OTPToken.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)

    otp = generate_otp()
    
    
    otp_hash = bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()
    expires_at = timezone.now() + timedelta(minutes=5)

    
    OTPToken.objects.create(
        user=user, 
        otp_hash=otp_hash, 
        purpose=purpose, 
        expires_at=expires_at
    )

    
    send_otp_email_task.delay(email, otp)
    
    return True

def verify_otp(email, purpose, otp_input):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise Exception("User not found")

    otp_obj = OTPToken.objects.filter(user=user, purpose=purpose, is_used=False).last()

    if not otp_obj or otp_obj.expires_at < timezone.now():
        raise Exception("OTP invalid or expired")

    if otp_obj.attempt_count >= 5:
        raise Exception("Too many attempts|0")

    
    if not bcrypt.checkpw(otp_input.encode(), otp_obj.otp_hash.encode()):
        otp_obj.attempt_count += 1
        otp_obj.save(update_fields=["attempt_count"])

        remaining = 5 - otp_obj.attempt_count

        if remaining <= 0:
            raise Exception("LOCKED")

        raise Exception(f"INVALID:{remaining}")

    otp_obj.is_used = True
    otp_obj.save(update_fields=["is_used"])

    if purpose == "email_verification":
        user.is_active = True
        user.is_email_verified = True
        user.save(update_fields=["is_active", "is_email_verified"])

    return user