from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task(name="send_otp_email_task")
def send_otp_email_task(email, otp):
    """
    Handles the slow SMTP network call in the background.
    """
    subject = "Verify your email - MFP"
    message = f"Hello,\n\nYour OTP is: {otp}\n\nThis expires in 5 minutes.\n\n- MFP Team"
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )