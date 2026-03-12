# 📦 Orders API Documentation

> **Base URL:** `/api/v1/orders/`  
> **Authentication:** Bearer JWT (`Authorization: Bearer <access_token>`)  
> **Content-Type:** `application/json`

All endpoints require authentication. Users can only access their own orders.

---

## 🎯 Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/checkout/` | POST | Create order from cart |
| `/` | GET | List my orders |
| `/{id}/` | GET | Get order details |
| `/{id}/cancel/` | POST | Cancel an order |

---

## 📋 Order Statuses

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
> ⚠️ These are **snapshots** - product changes after order won't affect this!

### OrderListItem (list view)
```json
{
  "id": 7,
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "order_number": "ORD-20260312-847291",
  "status": "pending",
  "payment_status": "unpaid",
  "payment_method": "mbank",
  "delivery_method": "courier",
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
  "payment_method": "mbank",
  "delivery_method": "courier",

  "customer_email": "user@example.com",
  "customer_phone": "+996700000001",
  "first_name": "Адиль",
  "last_name": "Тестов",
  "full_name": "Адиль Тестов",

  "country": "Kyrgyzstan",
  "city": "Bishkek",
  "address_line1": "Manas 10",
  "address_line2": "",
  "postal_code": "",
  "full_address": "Bishkek, Manas 10",
  "delivery_comment": "",

  "subtotal": "10000.00",
  "shipping_cost": "300.00",
  "discount_amount": "0.00",
  "total_amount": "10300.00",

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
> All timestamps are ISO 8601 UTC: `"2026-03-12T08:15:00Z"`

---

## 🛒 1. Create Order from Cart

**`POST /api/v1/orders/checkout/`**

Creates order from your cart. Does **everything atomically**: validates, snapshots products, deducts stock, clears cart.

### Request Body
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

| Field | Required | Notes |
|-------|:--------:|-------|
| `customer_phone` | ✅ | max 50 chars |
| `first_name` | ✅ | max 150 chars |
| `last_name` | ❌ | defaults to `""` |
| `city` | ✅ | max 120 chars |
| `address_line1` | ✅ | max 255 chars |
| `address_line2` | ❌ | defaults to `""` |
| `postal_code` | ❌ | max 30 chars |
| `delivery_comment` | ❌ | free text |
| `delivery_method` | ✅ | `courier` or `pickup` |
| `payment_method` | ✅ | `cash`, `card`, `mbank`, `elqr` |

### Responses

**✅ 201 Created**
Returns full `OrderDetail` object

**❌ 400 Bad Request**
```json
// Cart empty
{ "detail": "Your cart is empty." }

// Stock issue
{
  "detail": [
    "'SKU-CREAM-100ML': only 3 in stock (requested 5).",
    "'SKU-MASK-OLD': is no longer available."
  ]
}

// Field error
{
  "delivery_method": ["\"teleport\" is not a valid choice."]
}
```

**❌ 401 Unauthorized**
```json
{ "detail": "Authentication credentials were not provided." }
```

> ⚠️ **Atomic guarantee:** If anything fails, order not created, stock not deducted, cart intact.

---

## 📋 2. List My Orders

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
  "count": 2,
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
      "delivery_method": "courier",
      "total_amount": "7500.00",
      "total_items": 3,
      "created_at": "2026-03-10T12:00:00Z"
    }
  ]
}
```

---

## 🔍 3. Get Order Details

**`GET /api/v1/orders/{id}/`**

### Responses
| Code | Description |
|------|-------------|
| 200 | Full `OrderDetail` object |
| 404 | Order doesn't exist or isn't yours |
| 401 | Not authenticated |

---

## ❌ 4. Cancel Order

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

**❌ 404 Not Found** - Not your order or doesn't exist  
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
  "city": ["This field is required."]
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

### 📸 Snapshots
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
- Accessing others' orders returns `404` (not `403`) - prevents ID guessing

### 🔢 Order Number Format
`ORD-YYYYMMDD-XXXXXX`  
Example: `ORD-20260312-847291`

---

# how to simulate a payment:

As a **frontend developer** working with this Orders API, you usually **cannot fully simulate a real payment** (especially for `mbank` or `elqr`) because those are external mobile banking / QR systems — the backend most likely **does not** change `payment_status` to `paid` automatically after `/checkout/`.

Here are the **realistic ways** frontend developers usually handle "payment simulation / testing" in such projects (ranked from most common → least common):

| # | Method                              | How realistic? | Changes `payment_status`? | Best for                  | Effort |
|---|-------------------------------------|----------------|----------------------------|---------------------------|--------|
| 1 | Use **cash** payment method         | Very high      | Usually auto → `paid`      | Fastest day-to-day testing| ★☆☆☆☆ |
| 2 | Ask backend dev for **test / force-pay** endpoint or admin action | Highest        | Yes                        | Most convenient long-term | ★★☆☆☆ |
| 3 | Create order with `mbank`/`elqr` → wait / ask backend to mark paid manually | Medium         | Yes (after manual action)  | Realistic flow testing    | ★★★☆☆ |
| 4 | Create order → use `/cancel/` → create again (to test lifecycle) | Low            | No                         | Status & cancel testing   | ★★☆☆☆ |
| 5 | Mock the entire API response in frontend (MSW, MirageJS, etc.) | Very low       | Only in your browser       | UI/development before backend ready | ★★★★☆ |

### Most Practical Approaches Right Now

#### 1. Just use `payment_method: "cash"` (recommended for 90% of frontend work)

```jsonc
// POST /api/v1/orders/checkout/
{
  "customer_phone":   "+996700000001",
  "first_name":       "Адил",
  "last_name":        "Тест",
  "city":             "Bishkek",
  "address_line1":    "Test street 123",
  "delivery_method":  "courier",
  "payment_method":   "cash"          // ← key line
}
```

Many Kyrgyz / Central Asian shops treat **cash on delivery** as the "default testable" method.

Very often the backend automatically sets:

```json
payment_status: "paid",
paid_at:        "2026-03-12T08:45:00Z",
status:         "confirmed"   // or at least "pending"
```

→ You immediately see a "paid" order and can test further steps (list, detail, cancel if still allowed).

#### 2. Agree with backend developer on quick simulation helpers

Ask for one of these (choose 1–2 that are easiest for them):

- **Admin endpoint** (only you or test users can call)
  - `POST /api/v1/orders/{id}/simulate-pay/`
  - Body: `{ "payment_method": "mbank" }` or just empty
  - Sets `payment_status: "paid"`, `paid_at`, maybe moves `status` to `confirmed`

- **Magic test phone number** or **test email**
  - If you send `customer_phone: "+996999999999"` → auto-paid

- **Query param cheat code** (only in dev/staging)
  - `POST /api/v1/orders/checkout/?test=auto_pay`

- **Delayed auto-pay in dev** — after 10–30 seconds backend marks it paid

#### 3. Realistic flow for `mbank` / `elqr` (what you’ll show QA / PO)

1. Create order with `"payment_method": "mbank"`
2. Get 201 → see `payment_status: "unpaid"` in detail
3. Show beautiful "Pay with MBank" screen (or QR if you have it)
4. **Manually** ask backend colleague (or click admin button if exists):
   - "Please mark order #ORD-20260312-XXXX as paid via mbank"
5. Refresh order detail → see `paid`, `confirmed`, etc.

This is how most teams test external payment methods before real integration.

#### Quick summary – what to do today

Do this in this order:

1. Try creating with `"payment_method": "cash"` → check if `payment_status` becomes `"paid"` automatically
2. If yes → use it for almost everything (fastest)
3. If no → create orders with `mbank` / `elqr` and coordinate with backend to mark 1–2 test orders as paid when you need to test paid flow / cancel restriction / delivered flow
4. Ask backend: "Can we add a quick `/simulate-pay/` endpoint or magic phone number for frontend testing?"

Good luck with the checkout flow — Kyrgyz e-commerce projects usually live on `cash` + `mbank` for quite a long time 😄