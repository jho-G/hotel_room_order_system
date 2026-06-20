from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from menu.models import Category, MenuItem
from notifications.models import Notification
from notifications.services import notify_order_placed, notify_order_ready
from orders.models import Order, OrderItem
from rooms.models import Room


class NotificationTestMixin:
    def make_user(self, username, role):
        return User.objects.create_user(
            username=username, password="pass12345", role=role
        )

    def setUp(self):
        self.chef = self.make_user("chef", User.Role.CHEF)
        self.chef2 = self.make_user("chef2", User.Role.CHEF)
        self.waiter = self.make_user("waiter", User.Role.WAITER)
        self.supervisor = self.make_user("sup", User.Role.SUPERVISOR)

        self.room = Room.objects.create(room_number="101")
        self.category = Category.objects.create(name="Mains")
        self.item = MenuItem.objects.create(
            category=self.category, name="Tibs", price=350
        )

    def make_order(self, status=Order.Status.PENDING):
        order = Order.objects.create(room=self.room, status=status, total=350)
        OrderItem.objects.create(
            order=order, menu_item=self.item, quantity=1, price=350
        )
        return order


class NotificationServiceTests(NotificationTestMixin, TestCase):
    def test_order_placed_notifies_chefs_and_supervisors_only(self):
        order = self.make_order()
        notify_order_placed(order)

        recipients = set(
            Notification.objects.values_list("user__username", flat=True)
        )
        self.assertEqual(recipients, {"chef", "chef2", "sup"})
        self.assertFalse(
            Notification.objects.filter(user=self.waiter).exists()
        )

    def test_order_ready_notifies_waiters_only(self):
        order = self.make_order(Order.Status.COOKING)
        notify_order_ready(order)

        recipients = set(
            Notification.objects.values_list("user__username", flat=True)
        )
        self.assertEqual(recipients, {"waiter"})

    def test_inactive_users_are_not_notified(self):
        self.chef2.is_active = False
        self.chef2.save(update_fields=["is_active"])
        order = self.make_order()
        notify_order_placed(order)
        self.assertFalse(
            Notification.objects.filter(user=self.chef2).exists()
        )

    def test_new_notification_defaults_unread(self):
        order = self.make_order()
        notify_order_placed(order)
        self.assertTrue(
            Notification.objects.filter(user=self.chef, is_read=False).exists()
        )


class NotificationEndpointTests(NotificationTestMixin, TestCase):
    def test_fragment_scoped_to_current_user(self):
        Notification.objects.create(user=self.chef, title="For chef")
        Notification.objects.create(user=self.waiter, title="For waiter")

        self.client.force_login(self.chef)
        resp = self.client.get(reverse("notifications:fragment"))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "For chef")
        self.assertNotContains(resp, "For waiter")
        self.assertEqual(resp.context["unread_count"], 1)

    def test_fragment_requires_login(self):
        resp = self.client.get(reverse("notifications:fragment"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp.url)

    def test_mark_read_is_user_scoped(self):
        others = Notification.objects.create(user=self.waiter, title="Theirs")
        self.client.force_login(self.chef)

        resp = self.client.post(
            reverse("notifications:mark_read", args=[others.pk])
        )
        self.assertEqual(resp.status_code, 404)
        others.refresh_from_db()
        self.assertFalse(others.is_read)

    def test_mark_read_marks_own(self):
        own = Notification.objects.create(user=self.chef, title="Mine")
        self.client.force_login(self.chef)

        resp = self.client.post(
            reverse("notifications:mark_read", args=[own.pk])
        )
        self.assertEqual(resp.status_code, 200)
        own.refresh_from_db()
        self.assertTrue(own.is_read)

    def test_mark_all_read(self):
        Notification.objects.create(user=self.chef, title="a")
        Notification.objects.create(user=self.chef, title="b")
        other = Notification.objects.create(user=self.waiter, title="c")

        self.client.force_login(self.chef)
        resp = self.client.post(reverse("notifications:mark_all_read"))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            Notification.objects.filter(user=self.chef, is_read=False).count(), 0
        )
        other.refresh_from_db()
        self.assertFalse(other.is_read)  # untouched

    def test_list_page_shows_only_own(self):
        Notification.objects.create(user=self.chef, title="Chef item")
        Notification.objects.create(user=self.waiter, title="Waiter item")

        self.client.force_login(self.chef)
        resp = self.client.get(reverse("notifications:list"))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Chef item")
        self.assertNotContains(resp, "Waiter item")
