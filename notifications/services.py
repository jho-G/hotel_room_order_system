from accounts.models import User
from notifications.models import Notification


def notify_users(users, title, message=""):
    """Create one notification per user in a single query.

    ``users`` may be a queryset or any iterable of User instances.
    Returns the list of created Notification objects.
    """
    notifications = [
        Notification(user=user, title=title, message=message) for user in users
    ]
    if not notifications:
        return []
    return Notification.objects.bulk_create(notifications)


def _active_users_with_roles(*roles):
    return User.objects.filter(role__in=roles, is_active=True)


def notify_order_placed(order):
    """Alert chefs and supervisors that a new order has arrived."""
    recipients = _active_users_with_roles(User.Role.CHEF, User.Role.SUPERVISOR)
    title = f"New order #{order.pk}"
    message = (
        f"Room {order.room.room_number} placed an order — "
        f"ETB {order.total}."
    )
    return notify_users(recipients, title, message)


def notify_order_ready(order):
    """Alert waiters that an order is ready for delivery."""
    recipients = _active_users_with_roles(User.Role.WAITER)
    title = f"Order #{order.pk} ready"
    message = (
        f"Order for room {order.room.room_number} is ready for delivery."
    )
    return notify_users(recipients, title, message)
