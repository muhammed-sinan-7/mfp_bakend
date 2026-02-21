    
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.conf import settings
from common.models import SoftDeleteModel
from apps.industries.models import Industry



class Organization(SoftDeleteModel):
    name = models.CharField(max_length=255, unique=True)
    industry = models.ForeignKey(
        Industry,
        on_delete=models.SET_NULL,
        null=True
    )
    tagline = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class OrganizationMember(SoftDeleteModel):

    ROLE_CHOICES = (
        ("OWNER", "Owner"),
        ("ADMIN", "Admin"),
        ("EDITOR", "Editor"),
        ("VIEWER", "Viewer"),
    )

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="members"
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    joined_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.email} - {self.role}"
    


class OrganizationInvite(models.Model):

    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("EDITOR", "Editor"),
        ("VIEWER", "Viewer"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="invites"
    )

    email = models.EmailField()

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    token = models.UUIDField(default=uuid.uuid4, unique=True)

    is_accepted = models.BooleanField(default=False)

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=3)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invite: {self.email} → {self.organization.name}"