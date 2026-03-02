from django.db.models import Q, Min, Max, Count
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, BooleanFilter, CharFilter
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .models import (
    Category,
    Brand,
    Product,
    ProductVariant,
    Attribute,
    AttributeValue,
    ProductVariantAttribute,
    ProductVariantMultiAttribute,
)
from .serializers import (
    CategoryTreeSerializer,
    BrandSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    BrandFacetSerializer,
    PriceRangeFacetSerializer,
    AttributeFacetSerializer,
)


class ProductCursorPagination(CursorPagination):
    page_size = 40
    ordering = "-created_at"


class ProductFilterSet(FilterSet):
    is_active = BooleanFilter(field_name="is_active")
    category = CharFilter(field_name="category__slug")
    brand = CharFilter(field_name="brand__slug")
    price_min = CharFilter(method="filter_price_min")
    price_max = CharFilter(method="filter_price_max")

    class Meta:
        model = Product
        fields = ["is_active", "category", "brand"]

    def filter_price_min(self, queryset, name, value):
        try:
            return queryset.filter(min_price__gte=value)
        except (TypeError, ValueError):
            raise ValidationError({"price[min]": "Must be a number."})

    def filter_price_max(self, queryset, name, value):
        try:
            return queryset.filter(min_price__lte=value)
        except (TypeError, ValueError):
            raise ValidationError({"price[max]": "Must be a number."})


class ProductListAPIView(generics.ListAPIView):
    """
    GET /api/v1/products/
    """

    permission_classes = [AllowAny]
    pagination_class = ProductCursorPagination
    serializer_class = ProductListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilterSet
    search_fields = ["translations__name", "translations__description"]

    def get_queryset(self):
        qs = (
            Product.objects.filter(is_active=True)
            .select_related("category", "brand")
            .prefetch_related("translations", "images")
        )

        # Dynamic EAV filters: attr_{slug}
        params = self.request.query_params
        attr_params = {k: v for k, v in params.items() if k.startswith("attr_")}
        if attr_params:
            qs = self._apply_attribute_filters(qs, attr_params)

        # price[min] / price[max]
        price_min = params.get("price[min]")
        price_max = params.get("price[max]")
        if price_min is not None:
            try:
                qs = qs.filter(min_price__gte=price_min)
            except (TypeError, ValueError):
                raise ValidationError({"price[min]": "Must be a number."})
        if price_max is not None:
            try:
                qs = qs.filter(min_price__lte=price_max)
            except (TypeError, ValueError):
                raise ValidationError({"price[max]": "Must be a number."})

        return qs

    def _apply_attribute_filters(self, queryset, attr_params):
        for raw_key, raw_value in attr_params.items():
            # attr_ram -> ram
            slug = raw_key[len("attr_") :]
            try:
                attribute = Attribute.objects.get(slug=slug)
            except Attribute.DoesNotExist:
                raise ValidationError(
                    {"detail": f"Unknown attribute slug '{slug}'."}
                )

            values = self.request.query_params.getlist(raw_key) or [raw_value]
            value_qs = AttributeValue.objects.filter(
                attribute=attribute
            )

            if attribute.value_type == "int":
                value_qs = value_qs.filter(int__value__in=values)
            elif attribute.value_type == "float":
                value_qs = value_qs.filter(float__value__in=values)
            elif attribute.value_type == "boolean":
                bool_values = []
                for v in values:
                    if str(v).lower() in ("true", "1"):
                        bool_values.append(True)
                    elif str(v).lower() in ("false", "0"):
                        bool_values.append(False)
                value_qs = value_qs.filter(boolean__value__in=bool_values)
            else:
                value_qs = value_qs.filter(
                    Q(text__value__in=values)
                    | Q(color__value__in=values)
                )

            product_ids = ProductVariant.objects.filter(
                Q(single_attributes__attribute=attribute, single_attributes__value__in=value_qs)
                | Q(multi_attributes__attribute=attribute, multi_attributes__value__in=value_qs)
            ).values_list("product_id", flat=True)

            queryset = queryset.filter(id__in=product_ids)

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lang = self.request.query_params.get("lang", "ru")
        context["language"] = lang
        return context

    @extend_schema(
        summary="Список товаров с фильтрацией и поиском",
        description=(
            "Возвращает курсорно-пагинируемый список товаров.\n\n"
            "Поддерживает фильтры по категории, бренду, цене, активности и "
            "динамическим атрибутам вида attr_{slug}."
        ),
        parameters=[
            OpenApiParameter(
                name="category",
                description="Slug категории",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="brand",
                description="Slug бренда",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="price[min]",
                description="Минимальная цена",
                required=False,
                type=OpenApiTypes.NUMBER,
            ),
            OpenApiParameter(
                name="price[max]",
                description="Максимальная цена",
                required=False,
                type=OpenApiTypes.NUMBER,
            ),
            OpenApiParameter(
                name="search",
                description="Поиск по названию и описанию",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="lang",
                description="Язык переводов (ru, en, kg)",
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        tags=["Products"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ProductDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"
    queryset = (
        Product.objects.select_related("category", "brand")
        .prefetch_related(
            "translations",
            "images",
            "variants__images",
            "variants__single_attributes__attribute",
            "variants__single_attributes__value__translations",
            "variants__multi_attributes__attribute",
            "variants__multi_attributes__value__translations",
        )
    )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lang = self.request.query_params.get("lang", "ru")
        context["language"] = lang
        return context

    @extend_schema(
        summary="Детальная карточка товара",
        description="Возвращает товар по slug со всеми вариантами, изображениями и атрибутами.",
        tags=["Products"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CatalogSearchAPIView(ProductListAPIView):
    """
    GET /api/v1/catalog-search/

    Наследует фильтрацию товаров и добавляет фасеты.
    """

    @extend_schema(
        summary="Фасетный поиск по каталогу",
        description=(
            "Возвращает товары и агрегированные данные для построения фильтров: "
            "бренды, диапазон цен, значения атрибутов."
        ),
        tags=["Catalog"],
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        queryset = self.filter_queryset(self.get_queryset())

        brand_facets = self._build_brand_facets(queryset)
        price_range = self._build_price_range_facets(queryset)
        attribute_facets = self._build_attribute_facets(queryset)

        response.data = {
            "results": response.data["results"],
            "next": response.data.get("next"),
            "previous": response.data.get("previous"),
            "facets": {
                "brands": brand_facets,
                "price": price_range,
                "attributes": attribute_facets,
            },
        }
        return response

    def _build_brand_facets(self, queryset):
        lang = self.request.query_params.get("lang", "ru")
        qs = (
            queryset.exclude(brand__isnull=True)
            .values("brand__slug", "brand__translations__language", "brand__translations__name")
            .annotate(count=Count("id"))
        )
        by_slug = {}
        for row in qs:
            slug = row["brand__slug"]
            lang_code = row["brand__translations__language"]
            name = row["brand__translations__name"]
            count = row["count"]

            item = by_slug.setdefault(
                slug,
                {"slug": slug, "name_by_lang": {}, "count": 0},
            )
            item["name_by_lang"][lang_code] = name
            item["count"] += count

        data = []
        for slug, info in by_slug.items():
            name = info["name_by_lang"].get(lang) or info["name_by_lang"].get("ru")
            data.append(
                {
                    "slug": slug,
                    "name": name,
                    "count": info["count"],
                }
            )

        serializer = BrandFacetSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        return serializer.data

    def _build_price_range_facets(self, queryset):
        agg = queryset.aggregate(price_min=Min("min_price"), price_max=Max("min_price"))
        if agg["price_min"] is None or agg["price_max"] is None:
            return None
        serializer = PriceRangeFacetSerializer(
            data={"min": agg["price_min"], "max": agg["price_max"]}
        )
        serializer.is_valid(raise_exception=True)
        return serializer.data

    def _build_attribute_facets(self, queryset):
        product_ids = queryset.values_list("id", flat=True)
        variant_ids = ProductVariant.objects.filter(
            product_id__in=product_ids
        ).values_list("id", flat=True)

        value_ids = set(
            list(
                ProductVariantAttribute.objects.filter(
                    variant_id__in=variant_ids
                ).values_list("value_id", flat=True)
            )
            + list(
                ProductVariantMultiAttribute.objects.filter(
                    variant_id__in=variant_ids
                ).values_list("value_id", flat=True)
            )
        )
        values_qs = AttributeValue.objects.filter(id__in=value_ids).select_related(
            "attribute"
        ).prefetch_related("translations")

        lang = self.request.query_params.get("lang", "ru")

        counts = (
            ProductVariant.objects.filter(
                Q(single_attributes__value_id__in=value_ids)
                | Q(multi_attributes__value_id__in=value_ids)
            )
            .values("single_attributes__value_id", "multi_attributes__value_id")
            .annotate(count=Count("id"))
        )

        value_to_count = {}
        for row in counts:
            vid = row["single_attributes__value_id"] or row["multi_attributes__value_id"]
            value_to_count[vid] = value_to_count.get(vid, 0) + row["count"]

        facets_by_attr = {}
        for v in values_qs:
            translations = list(v.translations.all())
            by_lang = {t.language: t for t in translations}
            t = by_lang.get(lang) or by_lang.get("ru")
            attr_slug = v.attribute.slug

            facet = facets_by_attr.setdefault(
                attr_slug,
                {"attribute_slug": attr_slug, "values": []},
            )
            facet["values"].append(
                {
                    "id": v.id,
                    "value": v.typed_value,
                    "name": t.name if t else None,
                    "count": value_to_count.get(v.id, 0),
                }
            )

        facets = list(facets_by_attr.values())
        serializer = AttributeFacetSerializer(data=facets, many=True)
        serializer.is_valid(raise_exception=True)
        return serializer.data


class CategoryTreeAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CategoryTreeSerializer

    def get_queryset(self):
        return Category.objects.filter(parent__isnull=True).prefetch_related(
            "translations", "children__translations"
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lang = self.request.query_params.get("lang", "ru")
        context["language"] = lang
        return context

    @extend_schema(
        summary="Дерево категорий",
        description="Возвращает дерево категорий со всеми переводами.",
        tags=["Categories"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BrandListAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = BrandSerializer

    def get_queryset(self):
        return Brand.objects.prefetch_related("translations")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lang = self.request.query_params.get("lang", "ru")
        context["language"] = lang
        return context

    @extend_schema(
        summary="Список брендов",
        description="Возвращает список брендов с переводами.",
        tags=["Brands"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
