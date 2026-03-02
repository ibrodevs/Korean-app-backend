## Catalog API for frontend

Base URL: `/api/v1/`

### Language parameter

- **Query param**: `lang`
- **Values**: `ru` (default), `en`, `kg`
- **Effect**: Controls translations for names/descriptions in all endpoints below.

### 1. Product list

- **Endpoint**: `GET /api/v1/products/`
- **Description**: Cursor‑paginated list of products.

**Query params**

- **category**: category slug (e.g. `laptops`)
- **brand**: brand slug (e.g. `apple`)
- **price[min]**: minimal price
- **price[max]**: maximal price
- **is_active**: `true` / `false`
- **search**: full‑text search by translated name and description
- **attr_{slug}**: dynamic attribute filter, for example:
  - `attr_ram=16`
  - `attr_color[]=space-gray&attr_color[]=silver`

**Response (simplified)**

```json
{
  "next": "cursor-url-or-null",
  "previous": "cursor-url-or-null",
  "results": [
    {
      "id": 1,
      "slug": "igrovoi-noutbuk-asus-rog",
      "category": 10,
      "brand": 3,
      "is_active": true,
      "min_price": "999.00",
      "name": "Игровой ноутбук ASUS ROG",
      "description": "Короткое описание…",
      "main_image": {
        "id": 5,
        "image": "/media/products/2024/02/...",
        "alt": "ASUS ROG",
        "is_main": true,
        "order": 0,
        "variant_id": null
      }
    }
  ]
}
```

### 2. Product detail

- **Endpoint**: `GET /api/v1/products/{slug}/`
- **Description**: Full product card with variants, images and attributes.

**Path params**

- **slug**: product slug (e.g. `igrovoi-noutbuk-asus-rog`)

**Response (simplified)**

```json
{
  "id": 1,
  "slug": "igrovoi-noutbuk-asus-rog",
  "category": 10,
  "brand": 3,
  "is_active": true,
  "min_price": "999.00",
  "name": "Игровой ноутбук ASUS ROG",
  "description": "Полное описание…",
  "main_image": { "…": "…" },
  "images": [
    {
      "id": 5,
      "image": "/media/products/2024/02/...",
      "alt": "ASUS ROG общий вид",
      "is_main": true,
      "order": 0,
      "variant_id": null
    }
  ],
  "variants": [
    {
      "id": 101,
      "sku": "ROG-16-512-SPACEGRAY",
      "price": "999.00",
      "old_price": null,
      "stock": 5,
      "is_active": true,
      "is_default": true,
      "images": [/* изображения только для варианта */],
      "attributes": [
        {
          "attribute_slug": "ram",
          "attribute_id": 1,
          "value_id": 1001,
          "value": 16,
          "value_name": "16 ГБ"
        }
      ]
    }
  ],
  "created_at": "2024-02-01T12:00:00Z",
  "updated_at": "2024-02-10T12:00:00Z"
}
```

### 3. Faceted search

- **Endpoint**: `GET /api/v1/catalog-search/`
- **Description**: Same filters as `/products/`, plus aggregated facets for smart filters.

**Query params**

- Same as `/products/` (category, brand, price, search, `attr_{slug}`, `lang`).

**Response (simplified)**

```json
{
  "next": "cursor-or-null",
  "previous": "cursor-or-null",
  "results": [/* тот же формат, что и /products/ */],
  "facets": {
    "brands": [
      { "slug": "apple", "name": "Apple", "count": 12 }
    ],
    "price": {
      "min": "199.00",
      "max": "4999.00"
    },
    "attributes": [
      {
        "attribute_slug": "ram",
        "values": [
          { "id": 1001, "value": 8, "name": "8 ГБ", "count": 5 },
          { "id": 1002, "value": 16, "name": "16 ГБ", "count": 7 }
        ]
      }
    ]
  }
}
```

### 4. Categories tree

- **Endpoint**: `GET /api/v1/categories/`
- **Description**: Tree of categories for navigation.

**Response (simplified)**

```json
[
  {
    "id": 10,
    "slug": "laptops",
    "parent": null,
    "order": 0,
    "name": "Ноутбуки",
    "children": [
      {
        "id": 11,
        "slug": "gaming-laptops",
        "parent": 10,
        "order": 0,
        "name": "Игровые ноутбуки",
        "children": []
      }
    ]
  }
]
```

### 5. Brands list

- **Endpoint**: `GET /api/v1/brands/`
- **Description**: Flat list of brands for filters and landing pages.

**Response (simplified)**

```json
[
  {
    "id": 3,
    "slug": "apple",
    "name": "Apple"
  }
]
```

