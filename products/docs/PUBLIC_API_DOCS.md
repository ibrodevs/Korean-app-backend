# Korean App Backend - Public API Documentation

This document outlines the endpoints, parameters, and payloads required to integrate the frontend Client App with the public-facing product catalog API.

## 1. Global Configurations

### Base URL
All public catalog endpoints begin with the prefix: `/api/v1/`

### Authentication
All product catalog operations are fully public (`AllowAny`). Authentication is **not** required. Note that rate limits apply to anonymous users.

### Pagination (Standardized Limit/Offset)
All `LIST` and `Search` operations return paginated responses using the standard Limit/Offset pagination. The old `page` parameter is **not** supported.
- `limit`: The maximum number of items to return in a single page (Default: `40`, Max: `100`).
- `offset`: The starting position of the query (Default: `0`).

**Example Request:** `GET /api/v1/products/?limit=40&offset=80`

**Response format for paginated endpoints:**
```json
{
  "count": 142,
  "next": "http://api.com/api/v1/products/?limit=40&offset=120",
  "previous": "http://api.com/api/v1/products/?limit=40&offset=40",
  "results": [ ... ]
}
```

### Multi-Language Translations
All endpoints support the optional `?lang=` parameter to dictate the translation payload.
- `lang`: Defines which translation language to prioritize in the response (`ru`, `en`, `kg`, etc).
- Default: `ru`

---

## 2. API Endpoints

### 1. Catalog Search & Facets (Elasticsearch Powered)
`GET /api/v1/catalog-search/`
The primary endpoint for listing products with active filtering and aggregation to power frontend facet UIs.

**Filters Supported:**
- `category={slug}`: Filter by Exact Category Slug.
- `brand={slug}`: Filter by Exact Brand Slug.
- `price[min]={val}` & `price[max]={val}`: Filter by the product's minimum active price.
- `search={query}`: Multi-field Elasticsearch text search inside translated names and descriptions.
- `attr_{slug}={value}`: Dynamic EAV (Entity-Attribute-Value) filters. E.g., `?attr_color=#FF0000`, `?attr_ram=8GB`. Can accept multiple values: `?attr_color=red&attr_color=blue`.

**Pagination:**
Supports `?limit=Y&offset=Z`

**Response Addition (Facets):**
This endpoint returns an additional `"facets"` object at the root level alongside `"results"`, which computes active attribute counts based on the exact query:
```json
{
  "count": 15,
  "next": null,
  "previous": null,
  "results": [ ...products ],
  "facets": {
    "brands": [
      {"slug": "samsung", "name": "Samsung", "count": 10}
    ],
    "price": {"min": 100.0, "max": 1500.0},
    "attributes": [
      {
        "attribute_slug": "color",
        "values": [
          {"id": 5, "value": "#FF0000", "name": "Красный", "count": 10}
        ]
      }
    ]
  }
}
```

---

### 2. Product List (Standard SQL)
`GET /api/v1/products/`
A standard database-backed product listing (Does NOT return facets).

**Filters Supported:**
- Matches `catalog-search` filters: `?category=`, `?brand=`, `?price[min]=`, `?price[max]=`, and `?attr_{slug}=`.
- Replaces Elasticsearch's fuzzy text search with a standard SQL `?search=` filter.
- **Ordering:** `?ordering=-created_at` (default) or `?ordering=min_price`.

**Pagination:**
Supports `?limit=Y&offset=Z`

---

### 3. Product Detail
`GET /api/v1/products/{slug}/`
Retrieves a single product by its slug. The payload comprehensively includes all translated details, the brand, the category, and arrays of `variants`, `images`, and flattened `attributes`.

**Response Format Considerations:**
- Only Active products are returned.
- Attributes are expanded, showing the localized names (`name`) alongside raw typed values (`value`).

---

### 4. Category Tree
`GET /api/v1/categories/`
Recursively lists the entire Category tree payload (starting from root categories where `parent=null`).
- Translated automatically according to the `?lang=` parameter.
- Response is cached on the backend for 1 hour for high performance.
- Not paginated (returns the full nested array).

---

### 5. Brands List
`GET /api/v1/brands/`
Retrieves a flat list of all active Brands in the store.
- Translated automatically according to the `?lang=` parameter.
- Response is cached on the backend for 1 hour.
- Limit/Offset Paginated.

---

### Understanding Dynamic Attributes (EAV)
Products hold `attributes` inside their nested `Variant` arrays. 

When querying lists in endpoints 1 & 2 via dynamic query parameters like `?attr_size=XL`:
- The API intercepts variables beginning with `attr_`.
- Slices the string to find the Attribute matching slug `size`.
- Applies SQL (or elasticsearch) rules matching products containing a variant possessing that exact value securely.

### End of Documentation
