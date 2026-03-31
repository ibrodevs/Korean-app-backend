from django.db.models import Q, F as models_F
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, BooleanFilter, CharFilter
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import CursorPagination, LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework_extensions.cache.decorators import cache_response

from rest_framework.throttling import AnonRateThrottle

from .models import (
    Category,
    Brand,
    Product,
    ProductVariant,
    Attribute,
    AttributeValue,
)
from .documents import ProductDocument
from elasticsearch_dsl import Q
from django.db.models import Case, When
from .serializers import (
    CategoryTreeSerializer,
    BrandSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    BrandFacetSerializer,
    AttributeFacetSerializer,
)


class ProductCursorPagination(CursorPagination):
    page_size = 40
    ordering = "-created_at"

class ProductLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 40
    max_limit = 100


class ProductFilterSet(FilterSet):
    is_active = BooleanFilter(field_name="is_active")
    category = CharFilter(method="filter_category")
    brand = CharFilter(field_name="brand__slug")
    price_min = CharFilter(method="filter_price_min")
    price_max = CharFilter(method="filter_price_max")
    sale_only = BooleanFilter(method="filter_sale_only")
    in_stock_only = BooleanFilter(method="filter_in_stock_only")
    rating_min = CharFilter(method="filter_rating_min")
    tags = CharFilter(method="filter_tags")

    class Meta:
        model = Product
        fields = ["is_active", "category", "brand"]

    def filter_category(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset

        try:
            category = Category.objects.get(slug=value)
        except Category.DoesNotExist:
            return queryset.none()

        subtree = category.get_descendants(include_self=True)
        return queryset.filter(category__in=subtree)

    def filter_price_min(self, queryset, name, value):
        try:
            return queryset.filter(min_price__gte=value)
        except (TypeError, ValueError):
            raise ValidationError({"price_min": "Must be a number."})

    def filter_price_max(self, queryset, name, value):
        try:
            return queryset.filter(min_price__lte=value)
        except (TypeError, ValueError):
            raise ValidationError({"price_max": "Must be a number."})

    def filter_sale_only(self, queryset, name, value):
        if value:
            return queryset.filter(
                variants__is_active=True,
                variants__old_price__isnull=False,
                variants__old_price__gt=models_F("variants__price"),
            ).distinct()
        return queryset

    def filter_in_stock_only(self, queryset, name, value):
        if value:
            return queryset.filter(
                variants__is_active=True, variants__stock__gt=0
            ).distinct()
        return queryset

    def filter_rating_min(self, queryset, name, value):
        try:
            return queryset.filter(rating__gte=float(value))
        except (TypeError, ValueError):
            raise ValidationError({"rating_min": "Must be a number."})

    def filter_tags(self, queryset, name, value):
        tag_names = [t.strip() for t in value.split(",") if t.strip()]
        if tag_names:
            return queryset.filter(tags__name__in=tag_names).distinct()
        return queryset


class ProductListAPIView(generics.ListAPIView):
    """
    GET /api/v1/products/
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    pagination_class = ProductLimitOffsetPagination
    serializer_class = ProductListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilterSet
    search_fields = ["translations__name", "translations__description"]
    ordering_fields = ["min_price", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = (
            Product.objects.filter(is_active=True)
            .select_related("category", "brand")
            .prefetch_related(
                "translations",
                "images",
                "variants",
                "tags",
                "category__translations",
                "brand__translations",
            )
        )

        # Dynamic EAV filters: attr_{slug}
        params = self.request.query_params
        attr_params = {k: v for k, v in params.items() if k.startswith("attr_")}
        if attr_params:
            qs = self._apply_attribute_filters(qs, attr_params)

        return qs

    def _apply_attribute_filters(self, queryset, attr_params):
        for raw_key, raw_value in attr_params.items():
            # attr_ram -> ram
            slug = raw_key[len("attr_") :]
            try:
                attribute = Attribute.objects.get(slug=slug)
            except Attribute.DoesNotExist:
                continue

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

    @cache_response(timeout=60 * 5)  # 5 min — list cache; invalidate on product changes
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
                name="sale_only",
                description="Только товары со скидкой",
                required=False,
                type=OpenApiTypes.BOOL,
            ),
            OpenApiParameter(
                name="in_stock_only",
                description="Только товары в наличии",
                required=False,
                type=OpenApiTypes.BOOL,
            ),
            OpenApiParameter(
                name="rating_min",
                description="Минимальный рейтинг",
                required=False,
                type=OpenApiTypes.NUMBER,
            ),
            OpenApiParameter(
                name="tags",
                description="Фильтр по тегам (через запятую)",
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
            "tags",
            "category__translations",
            "brand__translations",
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

    @cache_response(timeout=60 * 15)  # 15 min — product detail rarely changes
    @extend_schema(
        summary="Детальная карточка товара",
        description="Возвращает товар по slug со всеми вариантами, изображениями и атрибутами.",
        tags=["Products"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CatalogSearchAPIView(generics.ListAPIView):
    """
    GET /api/v1/catalog-search/

    Использует Elasticsearch для фильтрации товаров и построения фасетов.
    """
    permission_classes = [AllowAny]
    serializer_class = ProductListSerializer
    throttle_classes = [AnonRateThrottle]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lang = self.request.query_params.get("lang", "ru")
        context["language"] = lang
        return context

    @extend_schema(
        summary="Фасетный поиск по каталогу (Elasticsearch)",
        description=(
            "Возвращает товары и агрегированные данные для построения фильтров: "
            "бренды, диапазон цен, значения атрибутов (рассчитывается в Elasticsearch)."
        ),
        tags=["Catalog"],
    )
    @cache_response(timeout=60 * 2)
    def list(self, request, *args, **kwargs):
        lang = request.query_params.get("lang", "ru")
        search = ProductDocument.search().filter("term", is_active=True)

        params = request.query_params

        # Filters
        if category := params.get("category"):
            search = search.filter("term", category__slug=category)

        if brand := params.get("brand"):
            search = search.filter("term", brand__slug=brand)

        if price_min := params.get("price[min]"):
            search = search.filter("range", min_price={"gte": float(price_min)})
        if price_max := params.get("price[max]"):
            search = search.filter("range", min_price={"lte": float(price_max)})

        if q := params.get("search"):
            search = search.query("multi_match", query=q, fields=["translations.name", "translations.description"])

        attr_params = {k: v for k, v in params.items() if k.startswith("attr_")}
        for raw_key, value in attr_params.items():
            slug = raw_key[len("attr_") :]
            values = params.getlist(raw_key) or [value]
            
            search = search.filter("nested", path="attributes", query=Q("bool", filter=[
                Q("term", attributes__attribute_slug=slug),
                Q("terms", attributes__value_text=values)
            ]))

        # Aggregations
        search.aggs.bucket('brands', 'terms', field='brand.slug', size=500)
        search.aggs.bucket('price_min', 'min', field='min_price')
        search.aggs.bucket('price_max', 'max', field='min_price')

        attr_agg = search.aggs.bucket('attributes', 'nested', path='attributes')
        attr_agg.bucket('by_value_id', 'terms', field='attributes.value_id', size=2000)

        # Sorting (newest first)
        search = search.sort('-created_at')

        # Pagination logic
        try:
            limit = int(params.get("limit", 40))
            if limit > 100:
                limit = 100
        except ValueError:
            limit = 40

        try:
            offset = int(params.get("offset", 0))
        except ValueError:
            offset = 0

        start = offset
        end = start + limit

        search = search[start:end]

        try:
            response = search.execute()
        except Exception as e:
            raise ValidationError({"detail": f"Elasticsearch query failed: {str(e)}"})

        # Facets processing
        brand_facets = self._format_brand_facets(response.aggregations.brands.buckets, lang)

        price_range = None
        if hasattr(response.aggregations, 'price_min') and response.aggregations.price_min.value is not None:
            price_range = {
                "min": response.aggregations.price_min.value,
                "max": response.aggregations.price_max.value
            }

        attribute_facets = self._format_attribute_facets(response.aggregations.attributes.by_value_id.buckets, lang)

        # Fetch actual Django models for DRF serializer
        product_ids = [hit.meta.id for hit in response]

        if product_ids:
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(product_ids)])
            qs = Product.objects.filter(id__in=product_ids).order_by(preserved)
            qs = qs.select_related("category", "brand").prefetch_related("translations", "images")
        else:
            qs = Product.objects.none()

        serializer = self.get_serializer(qs, many=True)

        # Pagination links
        count = response.hits.total.value
        base_url = request.build_absolute_uri(request.path)

        import urllib.parse
        def get_page_url(tgt_offset):
            query = request.query_params.copy()
            query['offset'] = tgt_offset
            query['limit'] = limit
            return f"{base_url}?{urllib.parse.urlencode(query, doseq=True)}"

        next_url = get_page_url(offset + limit) if end < count else None
        prev_url = get_page_url(max(0, offset - limit)) if offset > 0 else None

        return Response({
            "count": count,
            "next": next_url,
            "previous": prev_url,
            "results": serializer.data,
            "facets": {
                "brands": brand_facets,
                "price": price_range,
                "attributes": attribute_facets,
            },
        })

    def _format_brand_facets(self, buckets, lang):
        brand_slugs = [b.key for b in buckets]
        slug_to_count = {b.key: b.doc_count for b in buckets}

        if not brand_slugs:
            return []

        brands = Brand.objects.filter(slug__in=brand_slugs).prefetch_related("translations")

        data = []
        for b in brands:
            translations = list(b.translations.all())
            by_lang = {t.language: t for t in translations}
            t = by_lang.get(lang) or by_lang.get("ru")

            data.append({
                "slug": b.slug,
                "name": t.name if t else b.slug,
                "count": slug_to_count.get(b.slug, 0)
            })

        serializer = BrandFacetSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        return serializer.data

    def _format_attribute_facets(self, buckets, lang):
        value_to_count = {b.key: b.doc_count for b in buckets}
        value_ids = list(value_to_count.keys())

        if not value_ids:
            return []

        values_qs = AttributeValue.objects.filter(id__in=value_ids).select_related(
            "attribute"
        ).prefetch_related("translations")

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
    pagination_class = ProductLimitOffsetPagination

    def get_queryset(self):
        return Category.objects.filter(parent__isnull=True).prefetch_related(
            "translations", "children__translations"
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lang = self.request.query_params.get("lang", "ru")
        context["language"] = lang
        return context

    @cache_response(timeout=60 * 60)   # ← ДОБАВИТЬ
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
    pagination_class = ProductLimitOffsetPagination

    def get_queryset(self):
        return Brand.objects.prefetch_related("translations")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lang = self.request.query_params.get("lang", "ru")
        context["language"] = lang
        return context
        
    @cache_response(timeout=60 * 60)   # ← ДОБАВИТЬ
    @extend_schema(
        summary="Список брендов",
        description="Возвращает список брендов с переводами.",
        tags=["Brands"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
