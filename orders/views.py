from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiTypes
from rest_framework import generics, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .services import update_order_status, update_payment_status

from .models import Order, PickupLocation
from .serializers import (
    CheckoutSerializer,
    OrderCancelSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    PickupLocationSerializer,
)
from .services import cancel_order, create_order_from_cart


# ───────────────────────────────────────────────────────────────────────────────
# GET /orders/pickup-locations/
# ───────────────────────────────────────────────────────────────────────────────

class PickupLocationListAPIView(generics.ListAPIView):
    """
    Return all active pickup points sorted by sort_order, city, name.
    Frontend uses this to build the pickup-location selector at checkout.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PickupLocationSerializer
    queryset = PickupLocation.objects.filter(is_active=True)

    @extend_schema(
        summary="List active pickup locations",
        responses={200: PickupLocationSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)



# ─────────────────────────────────────────────────────────────────────────────
# POST /orders/checkout/
# ─────────────────────────────────────────────────────────────────────────────

class OrderCheckoutAPIView(APIView):
    """
    Create an order from the authenticated user's cart.

    Validates cart contents (stock, variant active status), creates a
    snapshot-based order, deducts stock, and clears the cart — all atomically.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Checkout — create order from cart",
        request=CheckoutSerializer,
        responses={
            201: OrderDetailSerializer,
            400: OpenApiTypes.OBJECT,
        },
    )
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = create_order_from_cart(
            user=request.user,
            data=serializer.validated_data,
        )

        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# GET /orders/
# ─────────────────────────────────────────────────────────────────────────────

class MyOrderListAPIView(generics.ListAPIView):
    """
    Return the paginated list of the authenticated user's orders.

    Supports filtering by ?status= and ?payment_status=
    """

    permission_classes = [IsAuthenticated]
    serializer_class = OrderListSerializer

    @extend_schema(
        summary="List my orders",
        responses={200: OrderListSerializer(many=True)},
    )
    def get_queryset(self):
        qs = (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related("items")
            .order_by("-created_at")
        )

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        payment_status_filter = self.request.query_params.get("payment_status")
        if payment_status_filter:
            qs = qs.filter(payment_status=payment_status_filter)

        return qs
    def get_object(self):
        """Возвращаем конкретный заказ пользователя или 404."""
        return get_object_or_404(
            Order.objects.prefetch_related("items"),
            pk=self.kwargs["pk"],
            user=self.request.user
        )

# ─────────────────────────────────────────────────────────────────────────────
# GET /orders/{id}/
# ─────────────────────────────────────────────────────────────────────────────

class MyOrderDetailAPIView(generics.RetrieveAPIView):
    """Return full details of one of the authenticated user's orders."""

    permission_classes = [IsAuthenticated]
    serializer_class = OrderDetailSerializer

    @extend_schema(
        summary="Get my order detail",
        responses={200: OrderDetailSerializer, 404: OpenApiTypes.OBJECT},
    )
    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related("items")
        )


# ─────────────────────────────────────────────────────────────────────────────
# POST /orders/{id}/cancel/
# ─────────────────────────────────────────────────────────────────────────────

class OrderCancelAPIView(APIView):
    """
    Cancel an order that is still in PENDING or CONFIRMED state.

    Stock is restored and an OrderStatusHistory entry is created.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Cancel my order",
        request=OrderCancelSerializer,
        responses={
            200: OrderDetailSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    def post(self, request, pk):
        serializer = OrderCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = get_object_or_404(Order, pk=pk, user=request.user)

        updated_order = cancel_order(
            order=order,
            reason=serializer.validated_data.get("reason", ""),
            changed_by=request.user,
        )

        return Response(
            OrderDetailSerializer(updated_order).data,
            status=status.HTTP_200_OK,
        )



# ─────────────────────────────────────────────────────────────────────────────
# POST /orders/{id}/update-status/
# ─────────────────────────────────────────────────────────────────────────────

class OrderUpdateStatusAPIView(APIView):
    """
    Update order status (for admin / webhook use).

    Uses services.update_order_status.
    """

    permission_classes = [IsAuthenticated]

    class StatusUpdateSerializer(serializers.Serializer):
        new_status = serializers.ChoiceField(choices=Order.Status.choices)
        comment = serializers.CharField(required=False, allow_blank=True, default="")

    @extend_schema(
        summary="Update order status",
        request=StatusUpdateSerializer,
        responses={200: OrderDetailSerializer, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    def post(self, request, pk):
        serializer = self.StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = get_object_or_404(Order, pk=pk)

        updated_order = update_order_status(
            order=order,
            new_status=serializer.validated_data["new_status"],
            comment=serializer.validated_data.get("comment", ""),
            changed_by=request.user,
        )

        return Response(OrderDetailSerializer(updated_order).data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# POST /orders/{id}/update-payment/
# ─────────────────────────────────────────────────────────────────────────────

class OrderUpdatePaymentAPIView(APIView):
    """
    Update order payment status (for webhook / payment provider callbacks).

    Uses services.update_payment_status.
    """

    permission_classes = [IsAuthenticated]

    class PaymentUpdateSerializer(serializers.Serializer):
        new_payment_status = serializers.ChoiceField(choices=Order.PaymentStatus.choices)
        comment = serializers.CharField(required=False, allow_blank=True, default="")

    @extend_schema(
        summary="Update order payment status",
        request=PaymentUpdateSerializer,
        responses={200: OrderDetailSerializer, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    def post(self, request, pk):
        serializer = self.PaymentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = get_object_or_404(Order, pk=pk)

        updated_order = update_payment_status(
            order=order,
            new_payment_status=serializer.validated_data["new_payment_status"],
            comment=serializer.validated_data.get("comment", ""),
            changed_by=request.user,
        )

        return Response(OrderDetailSerializer(updated_order).data, status=status.HTTP_200_OK)
