# Korean App Backend - Admin API Documentation

This document outlines the endpoints, parameters, and payloads required to integrate the frontend Admin Panel with the backend API. 

## 1. Global Configurations

### Base URL
All Admin endpoints begin with the prefix: `/api/admin/`

### Authentication
All endpoints are strictly protected by the `IsAdminUser` permission class. 
Every request must include a valid JWT token in the headers referencing an administrator account.
```http
Authorization: Bearer <your_access_token>
```

### Pagination (Standardized)
All LIST operations return paginated responses using standard Limit/Offset pagination. The `page` parameter is **not** supported.
- `limit`: The maximum number of items to return in a single page (Default: `20`, Max: `100`).
- `offset`: The starting position of the query (Default: `0`).

**Example Request:** `GET /api/admin/products/?limit=50&offset=100`

**Response Format:**
```json
{
  "count": 142,
  "next": "http://api.com/api/admin/products/?limit=50&offset=150",
  "previous": "http://api.com/api/admin/products/?limit=50&offset=50",
  "results": [ ... ]
}
```

---

## 2. API Endpoints

### Categories
`[GET, POST, PATCH, DELETE] /api/admin/categories/`
- Supports nested nested creation.
- **Search fields**: `?search=slug_or_translation_name`
- **Deleting** a category with linked products will return a `400 Bad Request` (Protected).
- **Payload Example (Creation)**:
```json
{
  "slug": "skincare",
  "parent": null,
  "translations": [
    {"language": "en", "name": "Skincare", "description": "Skin products"},
    {"language": "ru", "name": "Уход за кожей", "description": "Продукты для кожи"}
  ]
}
```

### Brands
`[GET, POST, PATCH, DELETE] /api/admin/brands/`
- **Search fields**: `?search=slug_or_translation_name`
- **Deleting** a brand will `SET_NULL` on all associated products (Products are retained).

### Attributes
`[GET, POST, PATCH, DELETE] /api/admin/attributes/`
- Manages attribute definitions (`color`, `size`, `weight`).
- `value_type` options: `"text", "int", "float", "boolean", "color"`
- `value_type` is **immutable** once created.
- `is_multiple`: Boolean flag whether products can hold an array of values (`True`) or a single value (`False`) for this attribute.

### Attribute Values
`[GET, POST, PATCH, DELETE] /api/admin/attribute-values/`
- Appends specific values to master Attributes.
- The `value` field accepts raw values and automatically casts them into their correct storage tables internally.
- **Boolean parsing**: Send `true`/`false`, `"true"`, `"1"`/`"0"`. Invalid strings will return `400`.
- **Color parsing**: Strict HEX validation enforces correct format (e.g., `#FF5500`).

---

### Products

#### CRUD & Details
`[GET, POST, PATCH, DELETE] /api/admin/products/`
- **Filters**:
  - `?category={slug}`
  - `?brand={slug}`
  - `?is_active=true|false`
  - `?price_min=10.00`
  - `?price_max=100.00`
  - `?search={query}`
- **Ordering**: `?ordering=min_price`, `?ordering=-min_price`, `?ordering=created_at`, `?ordering=-created_at`
- **Cascade Rules**: Deleting a product instantly cascaded into destroying its translations, variants, image links, and variant-to-attribute mappings.
- **Payload Example (Deep Creation)**: Note that errors in deep creations roll back the entire transaction instantly.
```json
{
  "slug": "some-product",
  "category": 1,
  "brand": 5,
  "translations": [
    {"language": "en", "name": "Some Product"}
  ],
  "variants": [
    {"sku": "SKU-001", "price": "19.99", "stock": 50, "is_default": true}
  ]
}
```

#### Bulk Product Create
`POST /api/admin/products/bulk/`
- Accepts an array of full Product deep-create payloads.
- Strictly atomic workflow: if *one* product chunk fails validation (e.g. invalid attribute, negative price, duplicate SKU), the entire batch rejects with a `400 Bad Request` and zeroes out the database writes.

#### Nested Variant Create
`POST /api/admin/products/{product_id}/variants/`
- Best for appending single variants to existing products.
- Evaluates `is_default` rules automatically. If a variant is created with `is_default=True`, the active default variant is automatically toggled `False`.
- Handles single vs multi attribute arrays strictly. Sending two values for an `is_multiple=False` attribute returns a `400`.

#### Nested Image Upload
`POST /api/admin/products/{product_id}/images/`
- Form-data required for file payload.
- Can map explicitly to a specific variant ID via payload payload or remain at the product level.

---

### Product Variants 

#### Bulk Update Pricing
`PATCH /api/admin/variants/bulk-price/`
- Atomic transaction processing.
- Automatically recalculates dynamic `min_price` caching fields back into the parent product tree.
```json
{
  "variants": [
    {"id": 10, "price": "45.00"},
    {"id": 12, "price": "22.50"}
  ]
}
```

#### Bulk Update Stock
`PATCH /api/admin/variants/bulk-stock/`
- Atomic transaction processing. Rejecting negative values stringently.
```json
{
  "variants": [
    {"id": 10, "stock": 100},
    {"id": 12, "stock": 0}
  ]
}
```

#### Detail Updates and Deletion
`[GET, PATCH, DELETE] /api/admin/variants/{id}/`
- Deleting a variant triggers a `min_price` recalculation on the parent automatically. Do not manually recalculate `min_price`. 
- Supports standard mapping array assignments explicitly defining variant attributes in update payloads.

---

### End of Documentation
