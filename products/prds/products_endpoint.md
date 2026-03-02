# Products API – GET /api/products/

This document explains how the frontend should use the **Products** endpoint.

## Endpoint

- **Method**: `GET`
- **URL**: `/api/products/`
- **Access**: Public (no authentication required)

## Query parameters

- **`category`** (required, string):
  - Controls which product category you are requesting.
  - Allowed values:
    - `women_clothes`
    - `men_clothes`
    - `kids_clothes`
    - `shoes`
    - `accessories`
    - `beauty`
    - `home`
    - `electronics`
    - `sports`
  - If this parameter is missing or invalid, the API returns **400 Bad Request** with a JSON error.

- **`lang`** (optional, string):
  - Controls the language of the `name` and `description` fields.
  - Allowed values: `ru`, `en`, `kg`
  - Default: `ru`

- **`cursor`** (optional, string):
  - Used for **cursor-based pagination**.
  - You normally do not construct this manually – you pass back the `next` value returned from the previous response.

## Pagination

The endpoint uses **cursor-based pagination** with:

- Page size: **40** items per page
- Ordering: newest first by `created_at` (internally the backend orders by `-created_at`)

The response body has the standard DRF cursor pagination shape:

```json
{
  "next": "http://localhost:8000/api/products/?category=women_clothes&cursor=cD0yMDI1LTAyLTI1KzEyJTNBMzMlM0EyNC41Njc4NzIlMkIwMCUzQTAw",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Some product name",
      "description": "Localized description",
      "price": "1999.99",
      "discount": 10,
      "...": "other fields, depend on category"
    }
  ]
}
```

- **`next`**:
  - URL to fetch the **next page**.
  - If `null`, there is no next page.
- **`previous`**:
  - URL to fetch the **previous page**.
  - If `null`, there is no previous page.
- **`results`**:
  - Array of product objects for the current page.

### How to paginate on the frontend

1. First request:
   - `GET /api/products/?category=women_clothes&lang=en`
2. To get the next page:
   - Read `response.next`.
   - If it is not `null`, call `GET` on that full URL.
3. To go back:
   - Use `response.previous` if it is not `null`.

## Response shape per category

All categories share some common fields:

- `id`
- `name` – localized based on `lang` (computed from `name_ru`, `name_en`, `name_kg`)
- `description` – localized based on `lang` (computed from `description_ru`, `description_en`, `description_kg`)
- `price`
- `discount`
- `created_at`
- `updated_at`

Each category also has category-specific fields. Some examples:

- `women_clothes`:
  - `size`, `color`, `material`, `season`, `brand`
- `men_clothes`:
  - `size`, `color`, `material`, `style`, `brand`
- `kids_clothes`:
  - `age_group`, `gender`, `color`, `material`
- `shoes`:
  - `size`, `color`, `material`, `season`, `brand`
- `accessories`:
  - `item_type`, `material`, `brand`, `color`
- `beauty`:
  - `product_type`, `purpose`, `ingredients`, `volume`, `shelf_life`
- `home`:
  - `item_type`, `material`, `dimensions`, `color`
- `electronics`:
  - `brand`, `model`, `ram`, `storage`, `processor`, `condition`, `warranty_months`
- `sports`:
  - `sport_type`, `size`, `material`, `level`

## Example requests

### Get first page of women clothes in Russian (default)

`GET /api/products/?category=women_clothes`

### Get first page of electronics in English

`GET /api/products/?category=electronics&lang=en`

### Use `next` cursor

If the response contains:

```json
{
  "next": "http://localhost:8000/api/products/?category=women_clothes&cursor=cD0yMDI1LTAyLTI1KzEyJTNBMzMlM0EyNC41Njc4NzIlMkIwMCUzQTAw",
  "previous": null,
  "results": [ ... ]
}
```

Then call:

`GET http://localhost:8000/api/products/?category=women_clothes&cursor=cD0yMDI1LTAyLTI1KzEyJTNBMzMlM0EyNC41Njc4NzIlMkIwMCUzQTAw`

The backend will keep the same sorting (`-created_at`) and page size (40).

