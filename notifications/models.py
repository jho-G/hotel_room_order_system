from django.conf import settings
from django.db import models


class Notification(models.Model):
    """A message addressed to a single staff user, surfaced in the bell dropdown."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"], name="notif_user_read_idx"),
        ]

    def __str__(self):
        return f"{self.title} → {self.user}"
