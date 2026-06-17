from django.db import models

from menu.models import MenuItem
from rooms.models import Room


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COOKING = "cooking", "Cooking"
        READY = "ready", "Ready"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} — Room {self.room.room_number}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return f"{self.quantity}× {self.menu_item.name}"

    @property
    def line_total(self):
        return self.price * self.quantity
