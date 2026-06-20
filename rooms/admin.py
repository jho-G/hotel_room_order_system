from django.contrib import admin
from django.utils.html import format_html

from rooms.models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_number", "unique_token", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("room_number", "unique_token")
    readonly_fields = (
        "unique_token",
        "menu_url_display",
        "qr_code_preview",
        "created_at",
    )

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return (
                (
                    None,
                    {
                        "fields": ("room_number", "is_active"),
                        "description": (
                            "Only enter the room number. The unique token, QR code, "
                            "and created date are generated automatically when you save."
                        ),
                    },
                ),
            )

        return (
            (None, {"fields": ("room_number", "is_active")}),
            (
                "Auto-generated",
                {
                    "fields": (
                        "unique_token",
                        "menu_url_display",
                        "qr_code_preview",
                        "created_at",
                    ),
                },
            ),
        )

    def menu_url_display(self, obj):
        url = obj.get_menu_url()
        if not url:
            return "N/A"
        return format_html('<a href="{0}" target="_blank">{0}</a>', url)

    menu_url_display.short_description = "Menu URL"

    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="150" style="background:#fff;border-radius:8px;" />'
                '<p><a href="{}" download>Download QR code</a></p>',
                obj.qr_code.url,
                obj.qr_code.url,
            )
        return "Save the room first to generate the QR code."

    qr_code_preview.short_description = "QR Code"
