from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from menu.models import Category, MenuItem
from notifications.models import Notification
from orders.models import Order, OrderItem
from orders.staff import (
    InvalidStatusTransition,
    mark_delivered,
    mark_ready,
    start_cooking,
)
from rooms.models import Room


class OrderTestMixin:
    def make_user(self, username, role):
        return User.objects.create_user(
            username=username, password="pass12345", role=role
        )

    def setUp(self):
        self.chef = self.make_user("chef", User.Role.CHEF)
        self.waiter = self.make_user("waiter", User.Role.WAITER)
        self.supervisor = self.make_user("sup", User.Role.SUPERVISOR)

        self.room = Room.objects.create(room_number="101")
        self.category = Category.objects.create(name="Mains")
        self.item = MenuItem.objects.create(
            category=self.category, name="Kitfo", price=400
        )

    def make_order(self, status=Order.Status.PENDING):
        order = Order.objects.create(room=self.room, status=status, total=400)
        OrderItem.objects.create(
            order=order, menu_item=self.item, quantity=1, price=400
        )
        return order


class StatusTransitionTests(OrderTestMixin, TestCase):
    """Service-layer transitions enforce the valid order lifecycle."""

    def test_full_happy_path(self):
        order = self.make_order(Order.Status.PENDING)
        start_cooking(order)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.COOKING)

        mark_ready(order)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.READY)

        mark_delivered(order)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DELIVERED)

    def test_cannot_start_cooking_non_pending(self):
        order = self.make_order(Order.Status.READY)
        with self.assertRaises(InvalidStatusTransition):
            start_cooking(order)

    def test_cannot_mark_ready_non_cooking(self):
        order = self.make_order(Order.Status.PENDING)
        with self.assertRaises(InvalidStatusTransition):
            mark_ready(order)

    def test_cannot_mark_delivered_non_ready(self):
        order = self.make_order(Order.Status.COOKING)
        with self.assertRaises(InvalidStatusTransition):
            mark_delivered(order)


class OrderActionPermissionTests(OrderTestMixin, TestCase):
    """Only the right role may perform each order action via the views."""

    def post_action(self, name, order):
        return self.client.post(reverse(name, args=[order.pk]))

    def test_chef_can_start_cooking(self):
        order = self.make_order(Order.Status.PENDING)
        self.client.force_login(self.chef)
        resp = self.post_action("orders:start_cooking", order)
        self.assertEqual(resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.COOKING)

    def test_waiter_cannot_start_cooking(self):
        order = self.make_order(Order.Status.PENDING)
        self.client.force_login(self.waiter)
        resp = self.post_action("orders:start_cooking", order)
        self.assertEqual(resp.status_code, 403)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_chef_can_mark_ready(self):
        order = self.make_order(Order.Status.COOKING)
        self.client.force_login(self.chef)
        resp = self.post_action("orders:mark_ready", order)
        self.assertEqual(resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.READY)

    def test_waiter_can_mark_delivered(self):
        order = self.make_order(Order.Status.READY)
        self.client.force_login(self.waiter)
        resp = self.post_action("orders:mark_delivered", order)
        self.assertEqual(resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DELIVERED)

    def test_chef_cannot_mark_delivered(self):
        order = self.make_order(Order.Status.READY)
        self.client.force_login(self.chef)
        resp = self.post_action("orders:mark_delivered", order)
        self.assertEqual(resp.status_code, 403)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.READY)

    def test_unauthenticated_cannot_act(self):
        order = self.make_order(Order.Status.PENDING)
        resp = self.post_action("orders:start_cooking", order)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp.url)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)


class OrderNotificationTests(OrderTestMixin, TestCase):
    """Order lifecycle events fan out notifications to the right roles."""

    def test_placing_order_notifies_chef_and_supervisor(self):
        self.client.post(
            reverse("orders:cart_add", args=[self.room.unique_token, self.item.pk])
        )
        resp = self.client.post(
            reverse("orders:checkout", args=[self.room.unique_token])
        )
        self.assertEqual(resp.status_code, 200)

        recipients = set(
            Notification.objects.values_list("user__role", flat=True)
        )
        self.assertEqual(
            recipients, {User.Role.CHEF, User.Role.SUPERVISOR}
        )

    def test_mark_ready_notifies_waiter(self):
        order = self.make_order(Order.Status.COOKING)
        mark_ready(order)
        self.assertTrue(
            Notification.objects.filter(user=self.waiter).exists()
        )
        self.assertFalse(
            Notification.objects.filter(user=self.chef).exists()
        )


class OrderDetailAccessTests(OrderTestMixin, TestCase):
    """Order detail visibility is scoped by role and order status."""

    def test_supervisor_sees_any_order(self):
        order = self.make_order(Order.Status.DELIVERED)
        self.client.force_login(self.supervisor)
        resp = self.client.get(reverse("orders:detail", args=[order.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_chef_cannot_view_ready_order(self):
        order = self.make_order(Order.Status.READY)
        self.client.force_login(self.chef)
        resp = self.client.get(reverse("orders:detail", args=[order.pk]))
        self.assertEqual(resp.status_code, 403)

    def test_waiter_cannot_view_pending_order(self):
        order = self.make_order(Order.Status.PENDING)
        self.client.force_login(self.waiter)
        resp = self.client.get(reverse("orders:detail", args=[order.pk]))
        self.assertEqual(resp.status_code, 403)
