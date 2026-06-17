from django.contrib import admin
from django.utils.html import format_html

from menu.models import Category, MenuItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "item_count")
    search_fields = ("name",)

    @admin.display(description="Items")
    def item_count(self, obj):
        return obj.items.count()


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "available",
        "image_preview",
    )
    list_filter = ("category", "available")
    list_editable = ("available",)
    search_fields = ("name", "description")
    readonly_fields = ("image_preview_large",)

    fieldsets = (
        (None, {"fields": ("category", "name", "description", "price", "available")}),
        ("Image", {"fields": ("image", "image_preview_large")}),
    )

    @admin.display(description="Image")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="48" height="48" style="object-fit:cover;border-radius:6px;" />',
                obj.image.url,
            )
        return "—"

    @admin.display(description="Preview")
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="200" style="object-fit:cover;border-radius:8px;" />',
                obj.image.url,
            )
        return "No image uploaded."
