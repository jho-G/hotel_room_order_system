from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.mixins import ChefRequiredMixin, RoleRequiredMixin, WaiterRequiredMixin
from accounts.models import User
from orders.models import Order
from orders.reports import get_daily_report, get_monthly_report
from orders.staff import (
    filter_supervisor_orders,
    get_chef_stats,
    get_cooking_orders,
    get_pending_orders,
    get_ready_orders,
    get_supervisor_stats,
    get_waiter_stats,
)


class SupervisorDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = "dashboard/supervisor.html"
    required_roles = (User.Role.SUPERVISOR,)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status_filter = self.request.GET.get("status", "")
        room_query = self.request.GET.get("room", "")

        context["page_title"] = "Supervisor Dashboard"
        context["page_subtitle"] = "Monitor orders, staff activity, and reports"
        context["stats"] = get_supervisor_stats()
        context["orders"] = filter_supervisor_orders(
            status=status_filter or None,
            room_query=room_query or None,
        )
        context["status_filter"] = status_filter
        context["room_query"] = room_query
        context["status_choices"] = Order.Status.choices
        return context


class ReportsView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = "dashboard/reports.html"
    required_roles = (User.Role.SUPERVISOR,)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        day = self._parse_day(self.request.GET.get("day"))
        year, month = self._parse_month(self.request.GET.get("month"))

        context["page_title"] = "Reports"
        context["page_subtitle"] = "Daily and monthly performance"
        context["daily"] = get_daily_report(day)
        context["monthly"] = get_monthly_report(year, month)
        return context

    @staticmethod
    def _parse_day(value):
        if value:
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                pass
        return timezone.localdate()

    @staticmethod
    def _parse_month(value):
        if value:
            try:
                parsed = datetime.strptime(value, "%Y-%m")
                return parsed.year, parsed.month
            except ValueError:
                pass
        today = timezone.localdate()
        return today.year, today.month


class ChefDashboardView(ChefRequiredMixin, TemplateView):
    template_name = "dashboard/chef.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Kitchen Dashboard"
        context["page_subtitle"] = "Receive orders and mark them ready"
        context["stats"] = get_chef_stats()
        context["pending_orders"] = get_pending_orders()
        context["cooking_orders"] = get_cooking_orders()
        return context


class WaiterDashboardView(WaiterRequiredMixin, TemplateView):
    template_name = "dashboard/waiter.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Delivery Dashboard"
        context["page_subtitle"] = "Pick up ready orders and deliver to rooms"
        context["stats"] = get_waiter_stats()
        context["ready_orders"] = get_ready_orders()
        return context
