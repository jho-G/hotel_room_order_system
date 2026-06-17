from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("supervisor/", views.SupervisorDashboardView.as_view(), name="supervisor"),
    path("chef/", views.ChefDashboardView.as_view(), name="chef"),
    path("waiter/", views.WaiterDashboardView.as_view(), name="waiter"),
]
