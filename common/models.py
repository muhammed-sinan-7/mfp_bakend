from django.db import models
from django.conf import settings
from django.utils import timezone

import uuid
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True




class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deleted_%(class)s_set"
    )

    # Managers
    objects = ActiveManager()        # default: only active
    all_objects = models.Manager()   # includes deleted

    class Meta:
        abstract = True

    def delete(self, user=None, *args, **kwargs):
        """
        Soft delete: mark record as deleted instead of removing it.
        """
        if self.is_deleted:
            return  

        self.is_deleted = True
        self.deleted_at = timezone.now()

        if user:
            self.deleted_by = user

        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

    def hard_delete(self):
        """
        Permanently remove from database.
        Use only for system cleanup tasks.
        """
        super().delete()

    def restore(self):
        """
        Restore soft deleted record.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])