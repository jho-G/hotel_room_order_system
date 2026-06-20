from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import ListView

from notifications.models import Notification

DROPDOWN_LIMIT = 8


def _user_notifications(user):
    return Notification.objects.filter(user=user)


def _render_dropdown(request):
    """Render the bell fragment (badge + recent list) for the current user."""
    qs = _user_notifications(request.user)
    return render(
        request,
        "components/notification_dropdown.html",
        {
            "notifications": qs[:DROPDOWN_LIMIT],
            "unread_count": qs.filter(is_read=False).count(),
        },
    )


class NotificationFragmentView(LoginRequiredMixin, View):
    """Polled every 5s; returns the badge + recent notifications via OOB swaps."""

    def get(self, request):
        return _render_dropdown(request)


class MarkNotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(
            _user_notifications(request.user), pk=pk
        )
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])
        return _render_dropdown(request)


class MarkAllReadView(LoginRequiredMixin, View):
    def post(self, request):
        _user_notifications(request.user).filter(is_read=False).update(is_read=True)
        return _render_dropdown(request)


class NotificationListView(LoginRequiredMixin, ListView):
    template_name = "notifications/list.html"
    context_object_name = "notifications"
    paginate_by = 30

    def get_queryset(self):
        return _user_notifications(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Notifications"
        context["page_subtitle"] = "Your recent alerts"
        return context
