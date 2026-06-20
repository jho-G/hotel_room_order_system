from django.db import transaction
from django.utils import timezone

from notifications.services import notify_order_ready
from orders.models import Order


class InvalidStatusTransition(Exception):
    pass


def _today_queryset():
    today = timezone.localdate()
    return Order.objects.filter(created_at__date=today)


def get_supervisor_stats():
    today_orders = _today_queryset()
    return {
        "orders_today": today_orders.count(),
        "pending": Order.objects.filter(status=Order.Status.PENDING).count(),
        "cooking": Order.objects.filter(status=Order.Status.COOKING).count(),
        "ready": Order.objects.filter(status=Order.Status.READY).count(),
        "delivered": today_orders.filter(status=Order.Status.DELIVERED).count(),
    }


def get_chef_stats():
    return {
        "pending": Order.objects.filter(status=Order.Status.PENDING).count(),
        "cooking": Order.objects.filter(status=Order.Status.COOKING).count(),
        "ready": Order.objects.filter(status=Order.Status.READY).count(),
    }


def get_waiter_stats():
    today = timezone.localdate()
    return {
        "ready": Order.objects.filter(status=Order.Status.READY).count(),
        "delivered_today": Order.objects.filter(
            status=Order.Status.DELIVERED,
            created_at__date=today,
        ).count(),
    }


def base_order_queryset():
    return Order.objects.select_related("room").prefetch_related(
        "items__menu_item__category"
    )


def get_pending_orders():
    return base_order_queryset().filter(status=Order.Status.PENDING)


def get_cooking_orders():
    return base_order_queryset().filter(status=Order.Status.COOKING)


def get_ready_orders():
    return base_order_queryset().filter(status=Order.Status.READY)


def filter_supervisor_orders(status=None, room_query=None):
    qs = base_order_queryset()
    if status:
        qs = qs.filter(status=status)
    if room_query:
        qs = qs.filter(room__room_number__icontains=room_query.strip())
    return qs


@transaction.atomic
def start_cooking(order):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != Order.Status.PENDING:
        raise InvalidStatusTransition("Only pending orders can be started.")
    order.status = Order.Status.COOKING
    order.save(update_fields=["status"])
    return order


@transaction.atomic
def mark_ready(order):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != Order.Status.COOKING:
        raise InvalidStatusTransition("Only cooking orders can be marked ready.")
    order.status = Order.Status.READY
    order.save(update_fields=["status"])
    notify_order_ready(order)
    return order


@transaction.atomic
def mark_delivered(order):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != Order.Status.READY:
        raise InvalidStatusTransition("Only ready orders can be marked delivered.")
    order.status = Order.Status.DELIVERED
    order.save(update_fields=["status"])
    return order
