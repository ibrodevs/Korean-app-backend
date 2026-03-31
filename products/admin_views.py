from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import ProtectedError
from django.db import transaction
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .views import ProductFilterSet

class AdminPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100

from .models import (
    Category,
    Brand,
    Product,
    ProductVariant,
    ProductImage,
    Attribute,
    AttributeValue,
)
from .admin_serializers import (
    AdminCategorySerializer,
    AdminBrandSerializer,
    AdminProductSerializer,
    AdminProductVariantSerializer,
    AdminProductImageSerializer,
    AdminAttributeSerializer,
    AdminAttributeValueSerializer,
    AdminProductVariantBulkPriceSerializer,
    AdminProductVariantBulkStockSerializer,
)


class AdminCategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().prefetch_related("translations")
    serializer_class = AdminCategorySerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    search_fields = ("translations__name", "slug")

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response({"error": "Cannot delete because there are associated items."}, status=status.HTTP_400_BAD_REQUEST)


class AdminBrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all().prefetch_related("translations")
    serializer_class = AdminBrandSerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    search_fields = ("translations__name", "slug")

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class AdminAttributeViewSet(viewsets.ModelViewSet):
    queryset = Attribute.objects.all().prefetch_related("translations")
    serializer_class = AdminAttributeSerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    search_fields = ("translations__name", "slug")


class AdminAttributeValueViewSet(viewsets.ModelViewSet):
    queryset = AttributeValue.objects.all().prefetch_related(
        "translations", "text", "int", "float", "boolean", "color", "attribute"
    )
    serializer_class = AdminAttributeValueSerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination


class AdminProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().select_related("category", "brand").prefetch_related(
        "translations",
        "variants__images",
        "variants__single_attributes__attribute",
        "variants__single_attributes__value__translations",
        "variants__single_attributes__value__text",
        "variants__single_attributes__value__int",
        "variants__single_attributes__value__float",
        "variants__single_attributes__value__boolean",
        "variants__single_attributes__value__color",
        "variants__multi_attributes__attribute",
        "variants__multi_attributes__value__translations",
        "variants__multi_attributes__value__text",
        "variants__multi_attributes__value__int",
        "variants__multi_attributes__value__float",
        "variants__multi_attributes__value__boolean",
        "variants__multi_attributes__value__color",
    )
    serializer_class = AdminProductSerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilterSet
    search_fields = ["translations__name", "slug"]
    ordering_fields = ["min_price", "created_at"]
    
    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"])
    def variants(self, request, pk=None):
        product = self.get_object()
        if request.method == "GET":
            variants = ProductVariant.objects.filter(product=product).prefetch_related("images")
            serializer = AdminProductVariantSerializer(variants, many=True)
            return Response(serializer.data)
        elif request.method == "POST":
            # Pass product from standard context or as a parameter
            # We must parse request.data to include product_id or we can just pass it to save
            serializer = AdminProductVariantSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
    @action(detail=True, methods=["post"])
    def images(self, request, pk=None):
        product = self.get_object()
        serializer = AdminProductImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all().select_related("product").prefetch_related("images")
    serializer_class = AdminProductVariantSerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    
    def destroy(self, request, *args, **kwargs):
        variant = self.get_object()
        product = variant.product
        response = super().destroy(request, *args, **kwargs)
        
        # update product min_price after variant deletion
        min_v = product.variants.filter(is_active=True).order_by("price").first()
        if min_v:
            product.min_price = min_v.price
            product.save(update_fields=["min_price"])
        else:
            product.min_price = 0  # No active variants left
            product.save(update_fields=["min_price"])
            
        return response
    
    @action(detail=False, methods=["patch"], url_path="bulk-price")
    def bulk_price(self, request):
        serializer = AdminProductVariantBulkPriceSerializer(data=request.data.get("variants", []), many=True)
        serializer.is_valid(raise_exception=True)

        updated_variants = []
        with transaction.atomic():
            for v_data in serializer.validated_data:
                try:
                    variant = ProductVariant.objects.get(id=v_data["id"])
                except ProductVariant.DoesNotExist:
                    return Response({"error": f"Variant with id {v_data['id']} does not exist."}, status=status.HTTP_400_BAD_REQUEST)
                variant.price = v_data["price"]
                variant.save(update_fields=["price"])
                
                # trigger product min_price update
                min_v = variant.product.variants.filter(is_active=True).order_by("price").first()
                if min_v:
                    variant.product.min_price = min_v.price
                    variant.product.save(update_fields=["min_price"])

                updated_variants.append(variant)
        
        return Response({"status": "Bulk price updated"})

    @action(detail=False, methods=["patch"], url_path="bulk-stock")
    def bulk_stock(self, request):
        serializer = AdminProductVariantBulkStockSerializer(data=request.data.get("variants", []), many=True)
        serializer.is_valid(raise_exception=True)

        updated_variants = []
        with transaction.atomic():
            for v_data in serializer.validated_data:
                try:
                    variant = ProductVariant.objects.get(id=v_data["id"])
                except ProductVariant.DoesNotExist:
                    return Response({"error": f"Variant with id {v_data['id']} does not exist."}, status=status.HTTP_400_BAD_REQUEST)
                variant.stock = v_data["stock"]
                variant.save(update_fields=["stock"])
                updated_variants.append(variant)
        return Response({"status": "Bulk stock updated"})
        
    @action(detail=True, methods=["post"])
    def images(self, request, pk=None):
        variant = self.get_object()
        serializer = AdminProductImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Note: Image could be linked to both product and variant to show in variant.
        serializer.save(variant=variant, product=variant.product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="attribute")
    def single_attribute(self, request, pk=None):
        variant = self.get_object()
        # Expecting {"attribute": "color", "value": "red"}
        from .admin_serializers import VariantAttributeWriteSerializer
        serializer = VariantAttributeWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Borrow _handle_attributes logic roughly
        admin_variant_serializer = AdminProductVariantSerializer()
        admin_variant_serializer._handle_attributes(variant, [serializer.validated_data])
        
        return Response({"status": "Attribute assigned"})
        
    @action(detail=True, methods=["post"], url_path="attributes")
    def multi_attributes(self, request, pk=None):
        variant = self.get_object()
        from .admin_serializers import VariantAttributeWriteSerializer
        # Expecting list of {"attribute": "size", "value": "L"}
        serializer = VariantAttributeWriteSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        
        admin_variant_serializer = AdminProductVariantSerializer()
        admin_variant_serializer._handle_attributes(variant, serializer.validated_data)
        
        return Response({"status": "Attributes assigned"})


class AdminProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all().select_related("product", "variant")
    serializer_class = AdminProductImageSerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
