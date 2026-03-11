from django.shortcuts import render
from rest_framework import generics
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import WriteUserSerializer, ListUserSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import CustomUser

# Create your views here.
class CreateUserAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = CustomUser.objects.all()
    serializer_class = WriteUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response(
            data = {
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone": user.phone,
                    "email": user.email,
                },
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                }
            }
        )

class UpdateUserAPIView(generics.UpdateAPIView):
    permission_classes = [AllowAny]
    queryset = CustomUser.objects.all()
    serializer_class = WriteUserSerializer


class ListUsers(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = CustomUser.objects.all()
    serializer_class = ListUserSerializer


class ListMeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ListUserSerializer(request.user)
        return Response(serializer.data)
    
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                data={"detail": "Successfully logged out"},
                status=status.HTTP_205_RESET_CONTENT
            )

        except TokenError:
            return Response(
                data={"detail": "Token is not valid or already blacklisted"},
                status=status.HTTP_400_BAD_REQUEST
            )


from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiTypes
from products.models import ProductVariant
from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    CartItemCreateSerializer,
    CartItemUpdateSerializer,
)


class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Получить текущую корзину",
        responses={200: CartSerializer}
    )
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart = (
            Cart.objects
            .prefetch_related("items__variant__product")
            .get(id=cart.id)
        )
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class CartItemCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Добавить товар в корзину",
        request=CartItemCreateSerializer,
        responses={201: CartSerializer, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        serializer = CartItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variant_id = serializer.validated_data["variant_id"]
        quantity = serializer.validated_data["quantity"]

        variant = ProductVariant.objects.select_related("product").get(
            id=variant_id,
            is_active=True,
            product__is_active=True,
        )

        if variant.stock < quantity:
            return Response(
                {"detail": "Недостаточно товара на складе."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            cart, _ = Cart.objects.get_or_create(user=request.user)

            cart_item, created = CartItem.objects.select_for_update().get_or_create(
                cart=cart,
                variant=variant,
                defaults={"quantity": quantity},
            )

            if not created:
                new_quantity = cart_item.quantity + quantity

                if variant.stock < new_quantity:
                    return Response(
                        {"detail": "Нельзя добавить больше, чем есть на складе."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                cart_item.quantity = new_quantity
                cart_item.save(update_fields=["quantity"])

        # Возвращаем обновленную корзину сразу
        cart = Cart.objects.prefetch_related("items__variant__product").get(id=cart.id)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class CartItemUpdateDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Обновить количество товара в корзине",
        request=CartItemUpdateSerializer,
        responses={200: CartSerializer, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def patch(self, request, item_id):
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data["quantity"]

        try:
            cart_item = CartItem.objects.select_related(
                "cart", "variant", "variant__product"
            ).get(
                id=item_id,
                cart__user=request.user,
            )
        except CartItem.DoesNotExist:
            return Response(
                {"detail": "Товар в корзине не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not cart_item.variant.is_active or not cart_item.variant.product.is_active:
            return Response(
                {"detail": "Этот товар сейчас неактивен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if cart_item.variant.stock < quantity:
            return Response(
                {"detail": "Недостаточно товара на складе."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_item.quantity = quantity
        cart_item.save(update_fields=["quantity"])

        card_id = cart_item.cart_id
        cart = Cart.objects.prefetch_related("items__variant__product").get(id=card_id)
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Удалить товар из корзины",
        responses={200: CartSerializer, 404: OpenApiTypes.OBJECT}
    )
    def delete(self, request, item_id):
        try:
            cart_item = CartItem.objects.get(
                id=item_id,
                cart__user=request.user,
            )
        except CartItem.DoesNotExist:
            return Response(
                {"detail": "Товар в корзине не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        cart_id = cart_item.cart_id
        cart_item.delete()
        
        cart = Cart.objects.prefetch_related("items__variant__product").get(id=cart_id)
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartClearAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Очистить корзину целиком",
        responses={200: CartSerializer, 404: OpenApiTypes.OBJECT}
    )
    def delete(self, request):
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            pass
            
        cart, _ = Cart.objects.prefetch_related("items__variant__product").get_or_create(user=request.user)
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)