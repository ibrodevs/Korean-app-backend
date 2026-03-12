# 📦 Orders API Documentation

> **Base URL:** `/api/v1/orders/`  
> **Authentication:** Bearer JWT (`Authorization: Bearer <access_token>`)  
> **Content-Type:** `application/json`

All endpoints require authentication. Users can only access their own orders.

---

## 🎯 Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/pickup-locations/` | GET | List active pickup points |
| `/checkout/` | POST | Create order from cart |
| `/` | GET | List my orders |
| `/{id}/` | GET | Get order details |
| `/{id}/cancel/` | POST | Cancel an order |

---

## 📋 Enums

### Order Status
| Status | Description | Can Customer Cancel? |
|--------|-------------|---------------------|
| `pending` | Order created, awaiting confirmation | ✅ Yes |
| `confirmed` | Order confirmed | ✅ Yes |
| `processing` | Being prepared | ❌ No |
| `shipped` | Handed to courier | ❌ No |
| `delivered` | Delivered | ❌ No |
| `canceled` | Canceled | - |
| `refunded` | Refunded | - |

### Payment Status
| Status | Description |
|--------|-------------|
| `unpaid` | Not yet paid |
| `paid` | Payment confirmed |
| `failed` | Payment failed |
| `refunded` | Full refund |
| `partially_refunded` | Partial refund |

### Payment Methods
| Value | Label |
|-------|-------|
| `cash` | Cash on delivery |
| `card` | Bank card |
| `mbank` | MBank (mobile) |
| `elqr` | ELQR (QR) |

### Delivery Methods
| Value | Label |
|-------|-------|
| `courier` | Courier delivery |
| `pickup` | Self-pickup |

---

## 📦 Response Objects

### PickupLocation
```json
{
  "id": 3,
  "city": "Bishkek",
  "name": "Main Office",
  "address": "Chui Ave 100",
  "address_line2": "",
  "latitude": "42.870000",
  "longitude": "74.590000",
  "phone": "+996312000001",
  "working_hours": "Mon–Sat 09:00–20:00"
}
```

### OrderItem (inside order details)
```json
{
  "id": 42,
  "product_name": "Корейский крем",
  "sku": "SKU-CREAM-100ML",
  "unit_price": "5000.00",
  "quantity": 2,
  "line_total": "10000.00"
}
```
> ⚠️ These are **snapshots** — product changes after order won't affect this!

### OrderListItem (list view)
```json
{
  "id": 7,
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "order_number": "ORD-20260312-847291",
  "status": "pending",
  "payment_status": "unpaid",
  "payment_method": "mbank",
  "delivery_method": "pickup",
  "total_amount": "10300.00",
  "total_items": 2,
  "created_at": "2026-03-12T08:15:00Z"
}
```

### OrderDetail (full view)
```json
{
  "id": 7,
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "order_number": "ORD-20260312-847291",
  "status": "pending",
  "payment_status": "unpaid",
  "payment_method": "cash",
  "delivery_method": "pickup",

  "customer_email": "user@example.com",
  "customer_phone": "+996700000001",
  "first_name": "Адиль",
  "last_name": "Тестов",
  "full_name": "Адиль Тестов",

  "country": "Kyrgyzstan",
  "city": "Bishkek",
  "address_line1": "Chui Ave 100",
  "address_line2": "",
  "postal_code": "",
  "full_address": "Bishkek, Chui Ave 100",
  "delivery_comment": "",

  "pickup_location": 3,
  "pickup_location_name": "Main Office",
  "pickup_city": "Bishkek",
  "pickup_address": "Chui Ave 100",

  "subtotal": "10000.00",
  "shipping_cost": "0.00",
  "discount_amount": "0.00",
  "total_amount": "10000.00",

  "notes": "",
  "total_items": 1,

  "items": [
    {
      "id": 42,
      "product_name": "Корейский крем",
      "sku": "SKU-CREAM-100ML",
      "unit_price": "5000.00",
      "quantity": 2,
      "line_total": "10000.00"
    }
  ],

  "paid_at": null,
  "confirmed_at": null,
  "shipped_at": null,
  "delivered_at": null,
  "canceled_at": null,
  "created_at": "2026-03-12T08:15:00Z",
  "updated_at": "2026-03-12T08:15:00Z"
}
```

> 💡 **Note:** All money fields are strings with 2 decimals: `"5000.00"`  
> All timestamps are ISO 8601 UTC or `null`.

---

## 📍 1. List Pickup Locations

**`GET /api/v1/orders/pickup-locations/`**

Returns all **active** pickup points, sorted by `sort_order → city → name`.  
Call this before the checkout screen to populate the pickup selector.

### Response 200 OK
```json
[
  {
    "id": 3,
    "city": "Bishkek",
    "name": "Main Office",
    "address": "Chui Ave 100",
    "address_line2": "",
    "latitude": "42.870000",
    "longitude": "74.590000",
    "phone": "+996312000001",
    "working_hours": "Mon–Sat 09:00–20:00"
  }
]
```

| Code | Description |
|------|-------------|
| 200 | List of active locations (may be empty `[]`) |
| 401 | Not authenticated |

---

## 🛒 2. Create Order from Cart

**`POST /api/v1/orders/checkout/`**

Creates order from your cart. Does **everything atomically**: validates, snapshots products, deducts stock, clears cart.

### Request Body — Courier delivery
```json
{
  "customer_phone": "+996700000001",
  "first_name": "Адиль",
  "last_name": "Тестов",
  "city": "Bishkek",
  "address_line1": "Manas 10",
  "address_line2": "",
  "postal_code": "",
  "delivery_comment": "Call 30 min before",
  "delivery_method": "courier",
  "payment_method": "mbank"
}
```

### Request Body — Pickup delivery
```json
{
  "customer_phone": "+996700000001",
  "first_name": "Адиль",
  "delivery_method": "pickup",
  "pickup_location_id": 3,
  "payment_method": "cash"
}
```

> For `pickup`, `city` and `address_line1` are **optional** — they are auto-filled from the pickup location.

### Field Reference

| Field | Required | Condition | Notes |
|-------|:--------:|-----------|-------|
| `customer_phone` | ✅ | always | max 50 chars |
| `first_name` | ✅ | always | max 150 chars |
| `last_name` | ❌ | — | defaults to `""` |
| `city` | ✅ | `courier` only | auto-filled for `pickup` |
| `address_line1` | ✅ | `courier` only | auto-filled for `pickup` |
| `address_line2` | ❌ | — | defaults to `""` |
| `postal_code` | ❌ | — | max 30 chars |
| `delivery_comment` | ❌ | — | free text |
| `delivery_method` | ✅ | always | `courier` or `pickup` |
| `pickup_location_id` | ✅ | `pickup` only | must be an active location ID |
| `payment_method` | ✅ | always | `cash`, `card`, `mbank`, `elqr` |

### Validation Rules

| Case | Error |
|------|-------|
| `delivery_method: pickup` + no `pickup_location_id` | `400` — `pickup_location_id` required |
| `delivery_method: pickup` + inactive location | `400` — location is inactive |
| `delivery_method: courier` + `pickup_location_id` provided | `400` — must be empty for courier |
| `delivery_method: courier` + no `city` | `400` — city required |
| `delivery_method: courier` + no `address_line1` | `400` — address required |

### Responses

**✅ 201 Created**  
Returns full `OrderDetail` object (including `pickup_location`, `pickup_location_name`, `pickup_city`, `pickup_address` for pickup orders)

**❌ 400 Bad Request**
```json
// Cart empty
{ "detail": "Your cart is empty." }

// Stock issue
{
  "detail": [
    "'SKU-CREAM-100ML': only 3 in stock (requested 5)."
  ]
}

// Pickup without location
{ "pickup_location_id": ["This field is required when delivery_method is 'pickup'."] }

// Courier + pickup_location_id provided
{ "pickup_location_id": ["Pickup location must be empty for courier delivery."] }
```

**❌ 401 Unauthorized**
```json
{ "detail": "Authentication credentials were not provided." }
```

> ⚠️ **Atomic guarantee:** If anything fails, order not created, stock not deducted, cart intact.

---

## 📋 3. List My Orders

**`GET /api/v1/orders/`**

Paginated list, newest first.

### Query Filters
| Param | Example | Description |
|-------|---------|-------------|
| `status` | `?status=pending` | Filter by order status |
| `payment_status` | `?payment_status=paid` | Filter by payment status |

### Response 200 OK
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 8,
      "uuid": "...",
      "order_number": "ORD-20260312-291847",
      "status": "delivered",
      "payment_status": "paid",
      "payment_method": "card",
      "delivery_method": "pickup",
      "total_amount": "7500.00",
      "total_items": 3,
      "created_at": "2026-03-10T12:00:00Z"
    }
  ]
}
```

---

## 🔍 4. Get Order Details

**`GET /api/v1/orders/{id}/`**

| Code | Description |
|------|-------------|
| 200 | Full `OrderDetail` object |
| 404 | Order doesn't exist or isn't yours |
| 401 | Not authenticated |

---

## ❌ 5. Cancel Order

**`POST /api/v1/orders/{id}/cancel/`**

Cancels order if status is `pending` or `confirmed`. Restores stock.

### Request Body
```json
{
  "reason": "Changed my mind"
}
```

| Field | Required | Notes |
|-------|:--------:|-------|
| `reason` | ❌ | Stored in history |

### Responses

**✅ 200 OK**  
Returns updated `OrderDetail` with `status: "canceled"`

**❌ 400 Bad Request**
```json
{
  "detail": "Order #ORD-20260312-847291 cannot be canceled (current status: shipped)."
}
```

**❌ 404 Not Found** — Not your order or doesn't exist  
**❌ 401 Unauthorized**

> ⚠️ **Idempotent:** Second cancel attempt on canceled order returns 400, stock not restored twice.

---

## 🔄 Order Lifecycle

```
pending → confirmed → processing → shipped → delivered → [done]
   ↳ canceled ←─┘           (refunded possible from delivered)
```

### Timestamps auto-set:
- `confirmed_at` when status → `confirmed`
- `shipped_at` when status → `shipped`
- `delivered_at` when status → `delivered`
- `canceled_at` when status → `canceled`
- `paid_at` when payment → `paid`

---

## 🚨 Error Handling

### Field Errors
```json
{
  "delivery_method": ["\"teleport\" is not a valid choice."],
  "city": ["City is required for courier delivery."]
}
```

### Business Logic Errors
```json
{ "detail": "Your cart is empty." }
```

### Multiple Errors (checkout stock)
```json
{
  "detail": [
    "'SKU-001': only 2 in stock (requested 5).",
    "'SKU-002': is no longer available."
  ]
}
```

### HTTP Status Codes
| Code | When |
|------|------|
| 200 | Success (GET, cancel) |
| 201 | Order created |
| 400 | Validation/business error |
| 401 | Missing/invalid token |
| 404 | Order not found or not yours |

---

## 💡 Key Design Points

### 📍 Pickup Location Snapshot
When `delivery_method: "pickup"`, the order stores both:
- **Live FK** `pickup_location` (set to `null` if the point is deleted — `SET_NULL`)
- **Snapshot fields** `pickup_location_name`, `pickup_city`, `pickup_address` — immutable after creation

This means historical orders always show the correct address even if the pickup point is renamed or deleted later.

Also, `city` and `address_line1` are auto-filled from the pickup location so that every order has a consistent address regardless of delivery method.

### 📸 Product Snapshots
Order items store product data **at time of purchase**:
- `product_name` from translation (prefers Russian)
- `sku` from variant
- `unit_price` from variant

Product changes later won't affect old orders.

### 🔒 Atomic Checkout
- All-or-nothing: if anything fails, nothing changes
- Prevents overselling (locks variants during checkout)
- Stock deducted only after all validations pass

### 💰 Financials
```
subtotal      = Σ (unit_price × quantity)
total_amount  = subtotal + shipping_cost - discount_amount
```
All money = `Decimal` with 2 decimal places (no float errors)

### 🛡️ Security
- All endpoints require JWT
- Can only see your own orders
- Accessing others' orders returns `404` (not `403`) — prevents order ID enumeration

### 🔢 Order Number Format
`ORD-YYYYMMDD-XXXXXX`  
Example: `ORD-20260312-847291`