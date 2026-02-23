from django.db import models
from django.utils import timezone
from encrypted_model_fields.fields import EncryptedTextField
from apps.organizations.models import Organization
from common.models import BaseModel
# Create your models here.


class SocialProvider(models.TextChoices):
    META = "META","Meta"
    LINKEDIN = "LINKEDIN","LinkedIn"
    YOUTUBE = "YOUTUBE",'YouTube'
    
    
class SocialAccount(BaseModel):
    organization = models.ForeignKey(Organization,
                                     on_delete=models.CASCADE,
                                     related_name="social_accounts")
    
    provider = models.CharField(
        max_length=20,
        choices=SocialProvider.choices
    )
    
    external_id = models.CharField(max_length=255)
    account_name = models.CharField(max_length=255)
    
    access_token = EncryptedTextField()
    refresh_token = EncryptedTextField(null=True, blank=True)
    
    token_expires_at = models.DateTimeField(blank=True,null=True)
    scopes = models.JSONField(default=list, blank=True)
    refresh_failed_count = models.IntegerField(default=0)
    last_refreshed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ("organization", "provider", "external_id")
        indexes = [
            models.Index(fields=["organization", "provider"]),
            models.Index(fields=["external_id"]),
        ]
        
    def is_token_expired(self):
        if not self.token_expires_at:
            return False
        return timezone.now() >= self.token_expires_at
    