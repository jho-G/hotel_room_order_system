from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from menu.models import Category, MenuItem
from orders.models import Order, OrderItem
from rooms.models import Room


class DashboardFactoryMixin:
    """Shared helpers for building staff users and sample orders."""

    def make_user(self, username, role):
        return User.objects.create_user(
            username=username, password="pass12345", role=role
        )

    def setUp(self):
        self.supervisor = self.make_user("sup", User.Role.SUPERVISOR)
        self.chef = self.make_user("chef", User.Role.CHEF)
        self.waiter = self.make_user("waiter", User.Role.WAITER)

        self.room = Room.objects.create(room_number="101")
        self.category = Category.objects.create(name="Mains")
        self.item = MenuItem.objects.create(
            category=self.category, name="Doro Wat", price=320
        )

    def make_order(self, status=Order.Status.PENDING, room=None):
        order = Order.objects.create(
            room=room or self.room, status=status, total=320
        )
        OrderItem.objects.create(
            order=order, menu_item=self.item, quantity=1, price=320
        )
        return order


class DashboardAccessTests(DashboardFactoryMixin, TestCase):
    """Each role may only reach its own dashboard."""

    def test_chef_dashboard_access_matrix(self):
        url = reverse("dashboard:chef")

        self.client.force_login(self.chef)
        self.assertEqual(self.client.get(url).status_code, 200)

        self.client.force_login(self.waiter)
        self.assertEqual(self.client.get(url).status_code, 403)

        self.client.force_login(self.supervisor)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_waiter_dashboard_access_matrix(self):
        url = reverse("dashboard:waiter")

        self.client.force_login(self.waiter)
        self.assertEqual(self.client.get(url).status_code, 200)

        self.client.force_login(self.chef)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_supervisor_dashboard_access_matrix(self):
        url = reverse("dashboard:supervisor")

        self.client.force_login(self.supervisor)
        self.assertEqual(self.client.get(url).status_code, 200)

        self.client.force_login(self.chef)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_unauthenticated_redirected_to_login(self):
        resp = self.client.get(reverse("dashboard:chef"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp.url)


class DashboardContentTests(DashboardFactoryMixin, TestCase):
    """Dashboards surface the right orders for each role."""

    def test_chef_sees_pending_and_cooking_only(self):
        pending = self.make_order(Order.Status.PENDING)
        cooking = self.make_order(Order.Status.COOKING)
        ready = self.make_order(Order.Status.READY)

        self.client.force_login(self.chef)
        resp = self.client.get(reverse("dashboard:chef"))

        pending_ids = {o.pk for o in resp.context["pending_orders"]}
        cooking_ids = {o.pk for o in resp.context["cooking_orders"]}
        self.assertEqual(pending_ids, {pending.pk})
        self.assertEqual(cooking_ids, {cooking.pk})
        self.assertNotIn(ready.pk, pending_ids | cooking_ids)

    def test_waiter_sees_ready_only(self):
        self.make_order(Order.Status.COOKING)
        ready = self.make_order(Order.Status.READY)

        self.client.force_login(self.waiter)
        resp = self.client.get(reverse("dashboard:waiter"))

        ready_ids = {o.pk for o in resp.context["ready_orders"]}
        self.assertEqual(ready_ids, {ready.pk})

    def test_supervisor_stats_counts(self):
        self.make_order(Order.Status.PENDING)
        self.make_order(Order.Status.COOKING)
        self.make_order(Order.Status.READY)
        self.make_order(Order.Status.DELIVERED)

        self.client.force_login(self.supervisor)
        resp = self.client.get(reverse("dashboard:supervisor"))
        stats = resp.context["stats"]

        self.assertEqual(stats["orders_today"], 4)
        self.assertEqual(stats["pending"], 1)
        self.assertEqual(stats["cooking"], 1)
        self.assertEqual(stats["ready"], 1)
        self.assertEqual(stats["delivered"], 1)

    def test_supervisor_filter_by_status_and_room(self):
        other_room = Room.objects.create(room_number="202")
        self.make_order(Order.Status.PENDING, room=self.room)
        target = self.make_order(Order.Status.READY, room=other_room)

        self.client.force_login(self.supervisor)

        resp = self.client.get(reverse("dashboard:supervisor"), {"status": "ready"})
        self.assertEqual({o.pk for o in resp.context["orders"]}, {target.pk})

        resp = self.client.get(reverse("dashboard:supervisor"), {"room": "202"})
        self.assertEqual({o.pk for o in resp.context["orders"]}, {target.pk})


class ReportsTests(DashboardFactoryMixin, TestCase):
    """Supervisor-only reports with delivered-only revenue."""

    def test_reports_supervisor_only(self):
        url = reverse("dashboard:reports")

        self.client.force_login(self.supervisor)
        self.assertEqual(self.client.get(url).status_code, 200)

        self.client.force_login(self.chef)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_daily_report_counts_and_revenue(self):
        # Two delivered (revenue), one pending (no revenue, but counts as order).
        self.make_order(Order.Status.DELIVERED)
        self.make_order(Order.Status.DELIVERED)
        self.make_order(Order.Status.PENDING)

        self.client.force_login(self.supervisor)
        daily = self.client.get(reverse("dashboard:reports")).context["daily"]

        self.assertEqual(daily["total_orders"], 3)
        self.assertEqual(daily["delivered_orders"], 2)
        self.assertEqual(daily["revenue"], 640)  # 2 × 320

    def test_monthly_top_items_only_counts_delivered(self):
        second = MenuItem.objects.create(
            category=self.category, name="Shiro", price=200
        )

        delivered = Order.objects.create(
            room=self.room, status=Order.Status.DELIVERED, total=720
        )
        OrderItem.objects.create(
            order=delivered, menu_item=self.item, quantity=2, price=320
        )
        OrderItem.objects.create(
            order=delivered, menu_item=second, quantity=1, price=200
        )
        # Pending order should NOT contribute to top items.
        pending = Order.objects.create(
            room=self.room, status=Order.Status.PENDING, total=320
        )
        OrderItem.objects.create(
            order=pending, menu_item=second, quantity=5, price=200
        )

        self.client.force_login(self.supervisor)
        monthly = self.client.get(reverse("dashboard:reports")).context["monthly"]
        top = monthly["top_items"]

        names = [row["menu_item__name"] for row in top]
        self.assertEqual(names, ["Doro Wat", "Shiro"])  # sorted by qty desc
        self.assertEqual(top[0]["quantity"], 2)
        self.assertEqual(top[0]["revenue"], 640)
        self.assertEqual(monthly["revenue"], 720)  # delivered only
