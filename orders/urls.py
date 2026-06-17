from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("<int:pk>/", views.OrderDetailView.as_view(), name="detail"),
    path("<int:pk>/start-cooking/", views.StartCookingView.as_view(), name="start_cooking"),
    path("<int:pk>/mark-ready/", views.MarkReadyView.as_view(), name="mark_ready"),
    path("<int:pk>/mark-delivered/", views.MarkDeliveredView.as_view(), name="mark_delivered"),
]
