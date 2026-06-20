import secrets

from django.db import models
from django.urls import reverse


class Room(models.Model):
    room_number = models.CharField(max_length=20, unique=True)
    unique_token = models.CharField(max_length=64, unique=True, editable=False)
    qr_code = models.ImageField(upload_to="qrcodes/", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["room_number"]

    def __str__(self):
        return f"Room {self.room_number}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and not self.unique_token:
            self.unique_token = self._generate_unique_token()
        super().save(*args, **kwargs)
        if is_new and not self.qr_code:
            from rooms.services import generate_room_qr_code

            generate_room_qr_code(self)

    @classmethod
    def _generate_unique_token(cls):
        while True:
            token = secrets.token_urlsafe(16)
            if not cls.objects.filter(unique_token=token).exists():
                return token

    def get_menu_path(self):
        return reverse("menu:customer_menu", kwargs={"token": self.unique_token})

    def get_menu_url(self, request=None):
        path = self.get_menu_path()
        if request is not None:
            return request.build_absolute_uri(path)
        from django.conf import settings
        
        base_url = getattr(settings, "SITE_URL", "http://localhost:8000")
        return f"{base_url.rstrip('/')}{path}"
