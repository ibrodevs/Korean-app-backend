from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiTypes

from products.models import Product
from .models import Favorite
from .serializers import FavoriteListSerializer, FavoriteCreateSerializer


class FavoriteListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List user's favorites",
        responses={200: FavoriteListSerializer(many=True)},
        tags=["Favorites"],
    )
    def get(self, request):
        favorites = (
            Favorite.objects
            .filter(user=request.user)
            .select_related("product")
            .prefetch_related("product__images", "product__variants", "product__translations")
        )
        lang = request.query_params.get("lang", "ru")
        serializer = FavoriteListSerializer(
            favorites, many=True, context={"request": request, "lang": lang}
        )

        return Response({
            "count": len(serializer.data),
            "results": serializer.data,
        })

    @extend_schema(
        summary="Add product to favorites",
        request=FavoriteCreateSerializer,
        responses={201: FavoriteListSerializer, 400: OpenApiTypes.OBJECT},
        tags=["Favorites"],
    )
    def post(self, request):
        serializer = FavoriteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        product = get_object_or_404(Product, id=product_id, is_active=True)

        _, created = Favorite.objects.get_or_create(
            user=request.user, product=product
        )

        if not created:
            return Response(
                {"detail": "Product is already in favorites."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        favorite = (
            Favorite.objects
            .select_related("product")
            .prefetch_related("product__images", "product__variants", "product__translations")
            .get(user=request.user, product=product)
        )
        lang = request.query_params.get("lang", "ru")
        out = FavoriteListSerializer(favorite, context={"request": request, "lang": lang})

        return Response(out.data, status=status.HTTP_201_CREATED)


class FavoriteDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Remove product from favorites",
        responses={204: None, 404: OpenApiTypes.OBJECT},
        tags=["Favorites"],
    )
    def delete(self, request, product_id):
        try:
            favorite = Favorite.objects.get(
                user=request.user, product_id=product_id
            )
        except Favorite.DoesNotExist:
            return Response(
                {"detail": "Favorite not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
