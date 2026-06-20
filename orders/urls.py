from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("<int:pk>/", views.OrderDetailView.as_view(), name="detail"),
    path("<int:pk>/start-cooking/", views.StartCookingView.as_view(), name="start_cooking"),
    path("<int:pk>/mark-ready/", views.MarkReadyView.as_view(), name="mark_ready"),
    path("<int:pk>/mark-delivered/", views.MarkDeliveredView.as_view(), name="mark_delivered"),
    
    # Customer cart and ordering actions
    path("cart/<str:token>/add/<int:item_id>/", views.AddToCartView.as_view(), name="cart_add"),
    path("cart/<str:token>/update/<int:item_id>/<str:action>/", views.UpdateCartQuantityView.as_view(), name="cart_update"),
    path("cart/<str:token>/checkout/", views.CheckoutView.as_view(), name="checkout"),
]
