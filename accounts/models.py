from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Staff user with role-based access (Supervisor, Chef, Waiter)."""

    class Role(models.TextChoices):
        SUPERVISOR = "supervisor", "Supervisor"
        CHEF = "chef", "Chef"
        WAITER = "waiter", "Waiter"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        blank=True,
        help_text="Staff role for dashboard access and permissions.",
    )

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_supervisor(self):
        return self.role == self.Role.SUPERVISOR

    @property
    def is_chef(self):
        return self.role == self.Role.CHEF

    @property
    def is_waiter(self):
        return self.role == self.Role.WAITER
