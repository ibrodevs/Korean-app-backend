
# PRD — CRUD Admin API for Product Catalog (DRF)

## 1. Overview

**What**
Admin CRUD API for managing an e-commerce product catalog including categories, brands, products, variants, images, attributes, and multilingual translations.

**Who**
Internal admin users operating a web admin panel to manage catalog data.

**Why**
To enable fast and centralized product catalog management through structured CRUD operations that support complex product structures (variants, attributes, translations).

---

# 2. Core Features

### 2.1 Category Management

CRUD operations for hierarchical product categories.

Important details:

* Categories use **tree structure (MPTT)**.
* Admins must be able to:

  * create root category
  * create child category
  * reorder categories
* Category translations supported.

Endpoints:

```
POST   /admin/categories/
GET    /admin/categories/
GET    /admin/categories/{id}/
PATCH  /admin/categories/{id}/
DELETE /admin/categories/{id}/
```

Translation endpoints:

```
POST   /admin/categories/{id}/translations/
PATCH  /admin/category-translations/{id}/
DELETE /admin/category-translations/{id}/
```

---

# 2.2 Brand Management

CRUD operations for brands.

Endpoints:

```
POST   /admin/brands/
GET    /admin/brands/
GET    /admin/brands/{id}/
PATCH  /admin/brands/{id}/
DELETE /admin/brands/{id}/
```

Brand translations:

```
POST   /admin/brands/{id}/translations/
PATCH  /admin/brand-translations/{id}/
DELETE /admin/brand-translations/{id}/
```

---

# 2.3 Product Management

CRUD operations for products.

Products include:

* category
* brand
* slug
* is_active
* min_price (computed or stored)

Endpoints:

```
POST   /admin/products/
GET    /admin/products/
GET    /admin/products/{id}/
PATCH  /admin/products/{id}/
DELETE /admin/products/{id}/
```

Product translations:

```
POST   /admin/products/{id}/translations/
PATCH  /admin/product-translations/{id}/
DELETE /admin/product-translations/{id}/
```

Translations include:

```
name
description
meta_title
meta_description
meta_keywords
```

---

# 2.4 Product Variant Management

Each product can have multiple variants.

Variant fields:

```
sku
price
old_price
stock
is_active
is_default
```

Endpoints:

```
POST   /admin/products/{product_id}/variants/
GET    /admin/products/{product_id}/variants/
PATCH  /admin/variants/{id}/
DELETE /admin/variants/{id}/
```

Rules:

* Only **one variant can be is_default = true**
* SKU must be unique.

---

# 2.5 Product Images

Images can belong to:

* product
* variant

Endpoints:

```
POST   /admin/products/{product_id}/images/
POST   /admin/variants/{variant_id}/images/

PATCH  /admin/images/{id}/
DELETE /admin/images/{id}/
```

Image fields:

```
image
alt
is_main
order
```

Rules:

* Only one image per product can be `is_main=true`.

---

# 2.6 Attribute Management

Attributes define product characteristics.

Example:

```
color
size
material
```

Supported types:

```
text
int
float
boolean
color
```

Endpoints:

```
POST   /admin/attributes/
GET    /admin/attributes/
PATCH  /admin/attributes/{id}/
DELETE /admin/attributes/{id}/
```

Translations:

```
POST   /admin/attributes/{id}/translations/
PATCH  /admin/attribute-translations/{id}/
```

---

# 2.7 Attribute Values

Attribute values depend on attribute type.

Examples:

```
Color → red
Size → 42
Weight → 1.5
```

Endpoints:

```
POST   /admin/attribute-values/
GET    /admin/attribute-values/
PATCH  /admin/attribute-values/{id}/
DELETE /admin/attribute-values/{id}/
```

System must automatically store value in correct table:

```
AttributeTextValue
AttributeIntValue
AttributeFloatValue
AttributeBooleanValue
AttributeColorValue
```

---

# 2.8 Assign Attributes to Product Variants

Variants can have:

* single attribute
* multi attribute

Tables used:

```
ProductVariantAttribute
ProductVariantMultiAttribute
```

Endpoints:

Single:

```
POST /admin/variants/{id}/attribute/
DELETE /admin/variant-attribute/{id}/
```

Multi:

```
POST /admin/variants/{id}/attributes/
DELETE /admin/variant-multi-attribute/{id}/
```

---

# 2.9 Filtering / Pagination / Sorting

Required for **Product list**.

Pagination:

```
limit
offset
page
```

Sorting:

```
price
-created_at
min_price
```

Filters:

```
category
brand
price range
attributes
is_active
```

Search integration with **Elasticsearch** is expected.

---

# 3. Non-Goals

Not included in this system:

* Order management
* Payment processing
* Shopping cart
* Checkout system
* Analytics dashboards
* AI recommendation engines
* ERP integrations

This API strictly manages **product catalog data**.

---

# 4. Tech Constraints

Stack:

```
Python
Django
Django REST Framework
PostgreSQL
Redis
Docker
Celery
```

Authentication:

```
JWT (rest_framework_simplejwt)
OAuth2 (Google login)
```

API Format:

```
JSON
```

Performance requirements:

* Avoid N+1 queries
* Use

```
select_related
prefetch_related
```

Search:

```
Elasticsearch integration
```

Documentation:

```
drf-spectacular
Swagger
Redoc
```

---

# 5. Success Criteria

API is considered complete when:

1️⃣ CRUD works for all models:

```
Category
Brand
Product
ProductVariant
ProductImage
Attribute
AttributeValue
```

2️⃣ Translations supported for:

```
Category
Brand
Product
Attribute
AttributeValue
```

3️⃣ Admin panel can:

* create products
* attach variants
* upload images
* assign attributes
* manage translations

4️⃣ Performance

```
<200ms for most read endpoints
```

5️⃣ API documentation auto-generated.

---

# 6. Phases

### Phase 1 — Base CRUD

Implement:

```
serializers
viewsets
routers
permissions
```

For:

```
Category
Brand
Product
Variant
Image
Attribute
AttributeValue
```

---

### Phase 2 — Admin Permissions

Add:

```
JWT authentication
Admin-only permissions
```

---

### Phase 3 — Filtering & Search

Add:

```
django-filter
Elasticsearch
product filtering
attribute filtering
```

---

### Phase 4 — Performance Optimization

Add:

```
Redis caching
query optimization
bulk operations
```

---

# 7. Agent Rules

### Always

* Use **DRF ViewSets + routers**
* Use **ModelSerializer**
* Use **transaction.atomic for complex writes**
* Validate business rules.

---

### Ask First

Before changing:

* database schema
* attribute system
* translation system
* variant logic.

---

### Never

Never:

* expose DELETE without authentication
* allow public product modification
* bypass validation rules
* introduce N+1 queries.

---

# Important Architecture Rule

For admin API:

```
/api/admin/*
```

Public API:

```
/api/catalog/*
```

Admin API must **not affect public API stability**.

---

---

# PRD — Part 2

# Architecture & Implementation Specification for Admin CRUD API

---

# 8. API Architecture

## Base API structure

API делится на **2 зоны**:

```
/api/admin/*
/api/catalog/*
```

Admin API используется **только админ панелью**.

Public API используется **витриной магазина**.

Admin API имеет:

```
Admin permissions
write operations
expanded responses
```

Public API имеет:

```
read only
optimized responses
cached
```

---

# 9. DRF Structure

Backend должен использовать следующую структуру.

```
catalog/
    models/
    serializers/
        category.py
        brand.py
        product.py
        variant.py
        attribute.py
    views/
        admin/
            category.py
            brand.py
            product.py
            variant.py
            attribute.py
        catalog/
            product.py
            category.py
    filters/
    services/
    permissions/
    urls/
```

---

# 10. View Architecture

Использовать **DRF ViewSets + routers**.

```
ModelViewSet
```

Example:

```python
class AdminProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = AdminProductSerializer
    permission_classes = [IsAdminUser]
```

Router:

```
/api/admin/products/
/api/admin/brands/
/api/admin/categories/
```

---

# 11. Serializer Design

Admin serializers должны поддерживать:

```
nested writes
translations
variant creation
image upload
attribute assignment
```

---

## Product serializer

Admin product serializer должен позволять:

```
create product
create translations
create variants
create images
```

Example request:

```
POST /admin/products
```

```
{
  "slug": "nike-air",
  "category": 1,
  "brand": 3,
  "translations": [
    {
      "language": "en",
      "name": "Nike Air",
      "description": "Running shoes"
    },
    {
      "language": "ru",
      "name": "Nike Air",
      "description": "Кроссовки"
    }
  ]
}
```

---

# 12. Variant Nested Creation

Variant creation endpoint:

```
POST /admin/products/{product_id}/variants
```

Example request:

```
{
  "sku": "NIKE-AIR-RED-42",
  "price": 120,
  "old_price": 150,
  "stock": 10,
  "is_default": true,
  "attributes": [
    {
      "attribute": "color",
      "value": "red"
    },
    {
      "attribute": "size",
      "value": 42
    }
  ]
}
```

System должен:

1️⃣ создать variant
2️⃣ создать ProductVariantAttribute
3️⃣ создать typed attribute values

---

# 13. Attribute Value Logic

Attribute values хранятся в разных таблицах.

```
AttributeTextValue
AttributeIntValue
AttributeFloatValue
AttributeBooleanValue
AttributeColorValue
```

Backend должен автоматически выбирать таблицу.

Pseudo logic:

```
if attribute.value_type == text
    create AttributeTextValue

if attribute.value_type == int
    create AttributeIntValue
```

---

# 14. Image Upload Design

Images должны загружаться через multipart.

Endpoint:

```
POST /admin/products/{id}/images
```

Request:

```
multipart/form-data
```

Fields:

```
image
alt
is_main
order
```

Если `is_main=true`:

```
previous main image must become false
```

---

# 15. Admin Optimized Endpoints

Admin panel должен получать **expanded data**.

Example:

```
GET /admin/products/{id}
```

Response:

```
{
  "id": 12,
  "slug": "nike-air",
  "category": {...},
  "brand": {...},

  "translations": [...],

  "variants": [
    {
      "id": 3,
      "sku": "nike-air-red",
      "price": 120,

      "attributes": [
        {
          "attribute": "color",
          "value": "red"
        }
      ],

      "images": [...]
    }
  ]
}
```

Это уменьшает **число API запросов в админке**.

---

# 16. Bulk Operations

Админка должна поддерживать **bulk операции**.

### Bulk create products

Endpoint:

```
POST /admin/products/bulk
```

Payload:

```
[
  {...product1},
  {...product2}
]
```

---

### Bulk price update

Endpoint:

```
PATCH /admin/variants/bulk-price
```

Payload:

```
{
  "variants": [
    {"id": 1, "price": 120},
    {"id": 2, "price": 140}
  ]
}
```

---

### Bulk stock update

Endpoint:

```
PATCH /admin/variants/bulk-stock
```

Payload:

```
{
  "variants": [
    {"id": 1, "stock": 10},
    {"id": 2, "stock": 5}
  ]
}
```

---

# 17. Filtering System

Использовать

```
django-filter
```

Example filters:

```
category
brand
price_min
price_max
is_active
```

Attribute filters:

```
color=red
size=42
```

---

# 18. Query Optimization Rules

Каждый queryset должен использовать:

```
select_related
prefetch_related
```

Example:

```python
Product.objects.select_related(
    "category",
    "brand"
).prefetch_related(
    "translations",
    "variants",
    "variants__images"
)
```

---

# 19. Elasticsearch Integration

Elasticsearch должен индексировать:

```
product name
description
brand
attributes
```

Index triggers:

```
product save
variant save
translation save
```

---

# 20. Permissions

Admin endpoints требуют:

```
IsAuthenticated
IsAdminUser
```

Variant deletion rule:

```
cannot delete default variant if only variant
```

---

# 21. Validation Rules

### Product

```
slug must be unique
```

### Variant

```
sku unique
only one default variant
price >= 0
stock >= 0
```

### Attribute

```
value type immutable
```

---

# 22. Transactions

Для сложных операций использовать:

```
transaction.atomic
```

Example:

```
create product
create translations
create variants
create attributes
```

---

# 23. Logging

Admin operations должны логироваться.

Log actions:

```
product created
product updated
variant updated
price changed
```

---

# 24. Testing Requirements

Tests required:

```
CRUD tests
permission tests
validation tests
bulk tests
```

Example:

```
test_create_product
test_variant_creation
test_attribute_assignment
```

---

# 25. Performance Targets

Admin API:

```
<300ms per request
```

Public API:

```
<150ms
```

---

# 26. AI Coding Constraints

AI coder должен:

Always:

```
use DRF ViewSets
use ModelSerializer
optimize queries
write tests
```

Ask first:

```
schema changes
attribute logic changes
translation system changes
```

Never:

```
introduce N+1 queries
duplicate attribute values
bypass permission checks
```

---

# Итог

Теперь PRD состоит из **2 частей**:

**Part 1**

* requirements
* business logic
* features

**Part 2**

* backend architecture
* API design
* serializer logic
* admin optimization
* performance rules

Этот PRD достаточно подробный чтобы **AI coder написал весь backend почти без уточнений**.

---


