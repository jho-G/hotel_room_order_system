import io

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile


def generate_room_qr_code(room, base_url=None):
    """Generate a QR code image for the room's in-room menu URL."""
    site_url = (base_url or settings.SITE_URL).rstrip("/")
    menu_url = f"{site_url}{room.get_menu_path()}"

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

    filename = f"room_{room.room_number}_{room.unique_token[:8]}.png"
    room.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
    room.save(update_fields=["qr_code"])
