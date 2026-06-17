from django.contrib import admin

from orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("menu_item", "quantity", "price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("pk", "room", "status", "total", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("room__room_number",)
    readonly_fields = ("created_at",)
    inlines = [OrderItemInline]
