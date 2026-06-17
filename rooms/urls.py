from django.urls import path

from . import views

app_name = "rooms"

urlpatterns = [
    path("", views.RoomListView.as_view(), name="list"),
    path("create/", views.RoomCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.RoomUpdateView.as_view(), name="edit"),
    path("<int:pk>/deactivate/", views.RoomDeactivateView.as_view(), name="deactivate"),
    path("<int:pk>/activate/", views.RoomActivateView.as_view(), name="activate"),
    path("<int:pk>/qr/download/", views.RoomDownloadQRView.as_view(), name="download_qr"),
]
