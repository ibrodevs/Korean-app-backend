# 🛡️ Authentication API Documentation

---

## 4.1 User Registration

**Endpoint:**  
`POST /api/auth/register/`

**Request Body:**

```json
{
  "first_name": "Kim",
  "last_name": "Min-su",
  "email": "kim@example.com",
  "phone": "+821012345678",
  "password": "StrongPass123!",
  "password_confirm": "StrongPass123!"
}


Successful Response (201 Created):

{
  "user": {
    "id": 12,
    "first_name": "Kim",
    "last_name": "Min-su",
    "phone": "358734572",
    "email": "kim@example.com"
  },
  "tokens": {
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token"
  }
}


Possible Validation Errors (400 Bad Request):
{
  "email": ["User with this email already exists"]
}



4.2 User Login

Endpoint:
POST /api/auth/login/

Request Body:

{
  "email": "kim@example.com",
  "password": "StrongPass123!"
}


Successful Response (200 OK):

{
  "user": {
    "id": 12,
    "first_name": "Kim ",
    "last_name": " Min-su",
    "phone" : "str",
    "email": "kim@example.com"
  },
  "tokens": {
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token"
  }
}

Error (401 Unauthorized):

{
  "detail": "Invalid credentials"
}

4.3 Refresh Access Token

Endpoint:
POST /api/auth/token/refresh/

Request Body:

{
  "refresh": "jwt_refresh_token"
}

Successful Response (200 OK):
{
  "access": "new_access_token"
}


4.4 Get Current User

Endpoint:
GET /api/auth/me/

Headers:

Authorization: Bearer <access_token>


Successful Response (200 OK):

{
  "id": 12,
  "first_name": "Kim",
  "last_name": "Min-su",
  "email": "kim@example.com",
  "photo": null,
  "phone": "+821012345678"
}

4.5 Logout

Endpoint:
POST /api/auth/logout/

Headers:
Authorization: Bearer <access_token>

Request Body:

{
  "refresh": "jwt_refresh_token"
}


Successful Response (205 Reset Content):

{
  "detail": "Successfully logged out"
}


✅ Notes for Frontend Developers

Use the access token in Authorization header for all protected routes (Bearer <token>).

Use the refresh token to get new access tokens or for logout.

Handle validation errors gracefully — they will come in the JSON body with descriptive messages.

Password rules: minimum 8 characters, at least one uppercase letter, at least one digit.