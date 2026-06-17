from django.urls import path

from . import views

app_name = "menu"

urlpatterns = [
    path("<str:token>/", views.CustomerMenuView.as_view(), name="customer_menu"),
]
