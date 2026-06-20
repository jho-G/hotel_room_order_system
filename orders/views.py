from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView

from accounts.mixins import (
    ChefRequiredMixin,
    RoleRequiredMixin,
    WaiterRequiredMixin,
)
from accounts.models import User
from orders.cart import (
    add_to_cart,
    decrease_quantity,
    get_cart_count,
    get_cart_lines,
    get_cart_total,
    increase_quantity,
)
from orders.models import Order
from orders.permissions import (
    user_can_mark_delivered,
    user_can_mark_ready,
    user_can_start_cooking,
    user_can_view_order,
)
from orders.services import (
    CartEmptyError,
    CartValidationError,
    create_order_from_cart,
)
from orders.staff import (
    InvalidStatusTransition,
    mark_delivered,
    mark_ready,
    start_cooking,
)
from rooms.models import Room


class OrderAccessMixin(LoginRequiredMixin, RoleRequiredMixin):
    """Ensure the staff user may access order views."""

    required_roles = (
        User.Role.SUPERVISOR,
        User.Role.CHEF,
        User.Role.WAITER,
    )

    def get_order_queryset(self):
        return Order.objects.select_related("room").prefetch_related(
            "items__menu_item__category"
        )

    def get_order(self):
        return get_object_or_404(self.get_order_queryset(), pk=self.kwargs["pk"])

    def check_order_access(self, order):
        if not user_can_view_order(self.request.user, order):
            raise PermissionDenied("You do not have permission to view this order.")


class OrderDetailView(OrderAccessMixin, DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_object(self):
        order = self.get_order()
        self.check_order_access(order)
        return order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        user = self.request.user
        context["page_title"] = f"Order #{order.pk}"
        context["page_subtitle"] = f"Room {order.room.room_number}"
        context["can_start_cooking"] = user_can_start_cooking(user, order)
        context["can_mark_ready"] = user_can_mark_ready(user, order)
        context["can_mark_delivered"] = user_can_mark_delivered(user, order)
        return context


class StartCookingView(ChefRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if not user_can_start_cooking(request.user, order):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            start_cooking(order)
        except InvalidStatusTransition as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f"Order #{order.pk} is now cooking.")
        return redirect(request.POST.get("next") or reverse("dashboard:chef"))


class MarkReadyView(ChefRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if not user_can_mark_ready(request.user, order):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            mark_ready(order)
        except InvalidStatusTransition as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f"Order #{order.pk} marked as ready.")
        return redirect(request.POST.get("next") or reverse("dashboard:chef"))


class MarkDeliveredView(WaiterRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if not user_can_mark_delivered(request.user, order):
            raise PermissionDenied("You do not have permission to perform this action.")
        try:
            mark_delivered(order)
        except InvalidStatusTransition as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                f"Order #{order.pk} delivered to room {order.room.room_number}.",
            )
        return redirect(request.POST.get("next") or reverse("dashboard:waiter"))


def _render_cart_fragment(request, room, cart=None, **extra):
    """Render the cart items partial for a given cart (or an empty cart)."""
    context = {
        "room": room,
        "cart_lines": get_cart_lines(cart) if cart is not None else [],
        "cart_total": get_cart_total(cart) if cart is not None else 0,
        "cart_count": get_cart_count(cart) if cart is not None else 0,
    }
    context.update(extra)
    return render(request, "components/customer_cart_items.html", context)


class AddToCartView(View):
    def post(self, request, token, item_id):
        room = get_object_or_404(Room, unique_token=token, is_active=True)
        cart = add_to_cart(request, token, item_id)
        return _render_cart_fragment(request, room, cart)


class UpdateCartQuantityView(View):
    def post(self, request, token, item_id, action):
        room = get_object_or_404(Room, unique_token=token, is_active=True)
        if action == "increase":
            cart = increase_quantity(request, token, item_id)
        elif action == "decrease":
            cart = decrease_quantity(request, token, item_id)
        else:
            return HttpResponseBadRequest("Invalid action")
        return _render_cart_fragment(request, room, cart)


class CheckoutView(View):
    def post(self, request, token):
        room = get_object_or_404(Room, unique_token=token, is_active=True)
        try:
            order = create_order_from_cart(request, token)
        except (CartEmptyError, CartValidationError) as e:
            return _render_cart_fragment(request, room, error_message=str(e))
        return _render_cart_fragment(
            request, room, order_success=True, order=order
        )
