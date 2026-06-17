from decimal import Decimal

from django.db import transaction

from menu.models import MenuItem
from orders.cart import clear_cart, get_cart_data, get_cart_lines
from orders.models import Order, OrderItem
from rooms.models import Room


class CartEmptyError(Exception):
    pass


class CartValidationError(Exception):
    pass


@transaction.atomic
def create_order_from_cart(request, room_token):
    """Create an order from the session cart inside a database transaction."""
    room = Room.objects.select_for_update().get(
        unique_token=room_token,
        is_active=True,
    )
    cart = get_cart_data(request, room_token)

    if not cart.get("items"):
        raise CartEmptyError("Your cart is empty.")

    lines = []
    total = Decimal("0.00")

    for item_id, quantity in cart["items"].items():
        try:
            menu_item = MenuItem.objects.select_for_update().get(
                pk=item_id,
                available=True,
            )
        except MenuItem.DoesNotExist as exc:
            raise CartValidationError(
                "One or more items are no longer available."
            ) from exc

        line_total = menu_item.price * quantity
        total += line_total
        lines.append(
            {
                "menu_item": menu_item,
                "quantity": quantity,
                "price": menu_item.price,
                "line_total": line_total,
            }
        )

    order = Order.objects.create(
        room=room,
        status=Order.Status.PENDING,
        total=total,
    )

    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                menu_item=line["menu_item"],
                quantity=line["quantity"],
                price=line["price"],
            )
            for line in lines
        ]
    )

    clear_cart(request)
    return order
