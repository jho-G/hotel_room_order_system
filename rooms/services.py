import io

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile


def generate_room_qr_code(room, base_url=None):
    """Generate a QR code image for the room's in-room menu URL."""
    # Fallback to localhost if SITE_URL is not configured
    site_url = (base_url or getattr(settings, "SITE_URL", "http://localhost:8000")).rstrip("/")
    
    # Use get_menu_path if it exists, otherwise fall back to a standard pattern
    menu_path = room.get_menu_path() if hasattr(room, "get_menu_path") else f"/rooms/{room.unique_token}/"
    menu_url = f"{site_url}{menu_path}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(menu_url)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    # Ensure we have a token slice for the filename; default to 'new' if not yet available
    token_slug = room.unique_token[:8] if room.unique_token else "new"
    filename = f"room_{room.room_number}_{token_slug}.png"
    room.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
    room.save(update_fields=["qr_code"])
