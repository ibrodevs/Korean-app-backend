from django.urls import path

from .views import (
    MyOrderDetailAPIView,
    MyOrderListAPIView,
    OrderCancelAPIView,
    OrderCheckoutAPIView,
)

urlpatterns = [
    # POST — create order from cart
    path("checkout/", OrderCheckoutAPIView.as_view(), name="order-checkout"),

    # GET  — list own orders  (?status=pending &payment_status=unpaid)
    path("", MyOrderListAPIView.as_view(), name="order-list"),

    # GET  — single order detail
    path("<int:pk>/", MyOrderDetailAPIView.as_view(), name="order-detail"),

    # POST — cancel order
    path("<int:pk>/cancel/", OrderCancelAPIView.as_view(), name="order-cancel"),
]
