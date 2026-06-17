from decimal import Decimal

from django.shortcuts import get_object_or_404

from menu.models import MenuItem

SESSION_CART_KEY = "customer_cart"


def _empty_cart(room_token):
    return {"room_token": room_token, "items": {}}


def get_cart_data(request, room_token):
    """Return cart dict scoped to the current room token."""
    cart = request.session.get(SESSION_CART_KEY)
    if not cart or cart.get("room_token") != room_token:
        cart = _empty_cart(room_token)
        request.session[SESSION_CART_KEY] = cart
        request.session.modified = True
    return cart


def save_cart(request, cart):
    request.session[SESSION_CART_KEY] = cart
    request.session.modified = True


def clear_cart(request):
    if SESSION_CART_KEY in request.session:
        del request.session[SESSION_CART_KEY]
        request.session.modified = True


def get_cart_count(cart):
    return sum(cart.get("items", {}).values())


def get_cart_total(cart):
    total = Decimal("0.00")
    for item_id, quantity in cart.get("items", {}).items():
        menu_item = MenuItem.objects.filter(pk=item_id, available=True).first()
        if menu_item:
            total += menu_item.price * quantity
    return total


def get_cart_lines(cart):
    """Return cart lines with menu item details for display and checkout."""
    lines = []
    for item_id, quantity in cart.get("items", {}).items():
        menu_item = get_object_or_404(MenuItem, pk=item_id, available=True)
        line_total = menu_item.price * quantity
        lines.append(
            {
                "menu_item": menu_item,
                "quantity": quantity,
                "line_total": line_total,
            }
        )
    return lines


def add_to_cart(request, room_token, item_id):
    cart = get_cart_data(request, room_token)
    item_key = str(item_id)
    get_object_or_404(MenuItem, pk=item_id, available=True)
    cart["items"][item_key] = cart["items"].get(item_key, 0) + 1
    save_cart(request, cart)
    return cart


def remove_from_cart(request, room_token, item_id):
    cart = get_cart_data(request, room_token)
    cart["items"].pop(str(item_id), None)
    save_cart(request, cart)
    return cart


def increase_quantity(request, room_token, item_id):
    return add_to_cart(request, room_token, item_id)


def decrease_quantity(request, room_token, item_id):
    cart = get_cart_data(request, room_token)
    item_key = str(item_id)
    if item_key not in cart["items"]:
        return cart
    cart["items"][item_key] -= 1
    if cart["items"][item_key] <= 0:
        del cart["items"][item_key]
    save_cart(request, cart)
    return cart
