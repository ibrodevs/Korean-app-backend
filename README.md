# Korean App Backend

Django REST Framework backend for a Korean cosmetics e-commerce platform.

## Stack

- Python 3.11, Django 4.x, Django REST Framework
- PostgreSQL (SQLite for local dev)
- SimpleJWT — authentication
- drf-spectacular — OpenAPI/Swagger docs
- Elasticsearch — faceted catalog search
- Redis — caching
- pytest — tests

---

## Quick Start

```bash
# 1. Clone & create virtualenv
python -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy env file and fill in variables
cp .env.example .env

# 4. Apply migrations
python manage.py migrate

# 5. Run dev server
python manage.py runserver
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | insecure key | Django secret key |
| `DEBUG` | `True` | Debug mode |
| `USE_SQLITE` | `False` | Use SQLite instead of PostgreSQL |
| `DATABASE_URL` | — | PostgreSQL connection string |
| `ALLOWED_HOSTS` | `*` | Comma-separated allowed hosts |
| `SENTRY_DSN` | — | Sentry DSN (optional) |

---

## API Docs

After running the server:

- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
- ReDoc: `http://localhost:8000/api/schema/redoc/`

---

## Auth Flow

### Register

```
POST /api/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "StrongPass1",
  "password_confirm": "StrongPass1",
  "first_name": "John",
  "last_name": "Doe"
}
```

Response:
```json
{
  "user": { "id": 1, "email": "user@example.com", ... },
  "tokens": { "access": "...", "refresh": "..." }
}
```

### Login

```
POST /api/auth/login/

{ "email": "user@example.com", "password": "StrongPass1" }
```

Response:
```json
{ "access": "...", "refresh": "..." }
```

### Use Token

```
Authorization: Bearer <access_token>
```

### Refresh Token

```
POST /api/auth/token/refresh/

{ "refresh": "..." }
```

### Logout

```
POST /api/auth/logout/
Authorization: Bearer <access_token>

{ "refresh": "..." }
```

### Google OAuth

```
POST /api/auth/google/

{ "id_token": "..." }         # mobile
{ "access_token": "..." }     # web
```

### Get Profile

```
GET /api/auth/me/
Authorization: Bearer <access_token>
```

### Update Profile

```
PATCH /api/auth/update/{id}/
Authorization: Bearer <access_token>
```

Only the owner or admin can update a profile.

---

## Catalog API

### List Products

```
GET /api/v1/products/
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Product ID |
| `name` | string | Translated name |
| `slug` | string | URL slug |
| `price` | decimal | Current price |
| `old_price` | decimal \| null | Price before discount |
| `image` | string \| null | Main image URL |
| `is_sale` | bool | `old_price > price` |
| `is_new` | bool | Created within last 7 days |
| `rating` | decimal | Average rating |
| `review_count` | int | Number of reviews |
| `stock_status` | string | `in_stock` / `low_stock` / `out_of_stock` |
| `tags` | array | List of tag names |

#### stock_status Logic

| Condition | Value |
|-----------|-------|
| `stock == 0` | `out_of_stock` |
| `stock < 5` | `low_stock` |
| `stock >= 5` | `in_stock` |

#### Filters

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `sale_only` | bool | `true` | Only products with discount |
| `in_stock_only` | bool | `true` | Only products in stock |
| `rating_min` | float | `4.0` | Minimum rating |
| `tags` | string | `beauty,popular` | Filter by tags (comma-separated) |
| `category` | string | `skincare` | Category slug |
| `price_min` | int | `10000` | Minimum price |
| `price_max` | int | `50000` | Maximum price |
| `search` | string | `крем` | Full-text search |
| `brand` | string | `laneige` | Brand slug |
| `lang` | string | `ru` | Translation language (ru/en/kg) |

Example:
```
GET /api/v1/products/?sale_only=true&rating_min=4&category=skincare
```

#### Pagination

```json
{
  "count": 120,
  "next": "...?limit=40&offset=40",
  "previous": null,
  "results": [...]
}
```

### Product Detail

```
GET /api/v1/products/{slug}/
```

Returns same fields as list + `variants`, `images`, `created_at`, `updated_at`.

### Categories

```
GET /api/v1/categories/
```

Returns hierarchical category tree.

### Brands

```
GET /api/v1/brands/
```

---

## Favorites API

All favorites endpoints require authentication (`Authorization: Bearer <token>`).

### Get Favorites

```
GET /api/v1/favorites/
```

Response:
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "product": {
        "id": 10,
        "name": "Product A",
        "price": 23000,
        "image": "...",
        "stock_status": "in_stock"
      }
    }
  ]
}
```

### Add to Favorites

```
POST /api/v1/favorites/

{ "product_id": 10 }
```

- Returns `201` on success
- Returns `400` if product already in favorites
- Returns `404` if product not found

### Remove from Favorites

```
DELETE /api/v1/favorites/{product_id}/
```

- Returns `204` on success
- Returns `404` if not in favorites

---

## Running Tests

```bash
pytest tests/ -v
```

Test coverage:
- Auth: register, login, protected endpoints, token refresh
- Catalog: list, detail, all filters, stock_status, is_sale
- Favorites: add, delete, duplicate protection, data isolation

---

## CI

GitHub Actions pipeline runs on every push to `main`:

1. Install dependencies
2. Lint (ruff + isort)
3. Run tests
