from django.urls import path

from notifications import views

app_name = "notifications"

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="list"),
    path("fragment/", views.NotificationFragmentView.as_view(), name="fragment"),
    path("read-all/", views.MarkAllReadView.as_view(), name="mark_all_read"),
    path("<int:pk>/read/", views.MarkNotificationReadView.as_view(), name="mark_read"),
]
