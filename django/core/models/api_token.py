import secrets

from django.db import models
from django.utils import timezone
from model_utils.models import TimeStampedModel

from core.schemas.capability_list import validate_capability_list


class ApiToken(TimeStampedModel):
    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="api_tokens"
    )
    name = models.CharField(
        max_length=255, help_text="A friendly name for this API token"
    )
    token = models.CharField(max_length=64, unique=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    capabilities = models.JSONField(
        default=list,
        help_text='List of capability objects, each with at least {"id": "<string>"}.',
    )

    class Meta:
        ordering = ["-created"]

    def clean(self):
        super().clean()
        validate_capability_list(self.capabilities, field_name="capabilities")

    def __str__(self):
        return f"{self.name} ({self.user.email})"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(32)  # 64 character hex string
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return self.is_active and not self.is_expired

    def mark_as_used(self):
        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at", "modified"])
