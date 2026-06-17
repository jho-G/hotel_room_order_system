from accounts.models import User
from orders.models import Order


def user_can_view_order(user, order):
    """Return True if the staff user may view this order."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.role == User.Role.SUPERVISOR:
        return True
    if user.role == User.Role.CHEF and order.status in (
        Order.Status.PENDING,
        Order.Status.COOKING,
    ):
        return True
    if user.role == User.Role.WAITER and order.status in (
        Order.Status.READY,
        Order.Status.DELIVERED,
    ):
        return True
    return False


def user_can_start_cooking(user, order):
    return (
        user.is_authenticated
        and (user.is_superuser or user.role == User.Role.CHEF)
        and order.status == Order.Status.PENDING
    )


def user_can_mark_ready(user, order):
    return (
        user.is_authenticated
        and (user.is_superuser or user.role == User.Role.CHEF)
        and order.status == Order.Status.COOKING
    )


def user_can_mark_delivered(user, order):
    return (
        user.is_authenticated
        and (user.is_superuser or user.role == User.Role.WAITER)
        and order.status == Order.Status.READY
    )
