from django.urls import path

from . import views

app_name = "menu"

urlpatterns = [
    # Category management
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/create/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_edit"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),

    # Menu item management
    path("items/", views.MenuItemListView.as_view(), name="item_list"),
    path("items/create/", views.MenuItemCreateView.as_view(), name="item_create"),
    path("items/<int:pk>/edit/", views.MenuItemUpdateView.as_view(), name="item_edit"),
    path("items/<int:pk>/delete/", views.MenuItemDeleteView.as_view(), name="item_delete"),
    path("items/<int:pk>/toggle-availability/", views.MenuItemToggleAvailabilityView.as_view(), name="item_toggle_availability"),

    # Customer facing (moved to bottom to avoid shadowing other paths)
    path("<str:token>/", views.CustomerMenuView.as_view(), name="customer_menu"),
]
