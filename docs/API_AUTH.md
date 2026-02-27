# FinanceAI – Authentication API

Base URL (when running locally): `http://localhost:8000/api/auth`

All auth responses use a consistent envelope:

- **Success:** `{ "status": "success", "data": { ... } }`
- **Error:** `{ "status": "error", "message": "Human-readable message" }`  
  Validation errors may include an optional `errors` object with field-level details.

---

## 1. Register (create account)

**POST** `/api/auth/register/`

Creates a new user and returns JWT tokens (user is logged in).

### Headers

| Header           | Value              |
|-----------------|--------------------|
| `Content-Type`  | `application/json` |

CSRF is not required for this endpoint (exempt for API use).

### Request body (JSON)

| Field              | Type   | Required | Description |
|--------------------|--------|----------|-------------|
| `username`         | string | No*      | Unique username; if omitted, derived from email prefix |
| `email`            | string | Yes      | Valid email (stored lowercased) |
| `password`         | string | Yes      | Min 8 chars, at least one letter and one number |
| `first_name`       | string | No       | Given name |
| `last_name`        | string | No       | Family name |
| `risk_appetite`    | string | No       | `conservative` \| `moderate` \| `aggressive` (default: `moderate`) |
| `experience_level` | string | No       | `beginner` \| `intermediate` \| `advanced` (default: `beginner`) |

\* If `username` is omitted, it is generated from the part before `@` in `email`; if that is taken, a number suffix is added.

### Example request

```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass1",
  "first_name": "John",
  "last_name": "Doe",
  "risk_appetite": "moderate",
  "experience_level": "beginner"
}
```

### Success response (201 Created)

```json
{
  "status": "success",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "profile": {
        "risk_appetite": "moderate",
        "experience_level": "beginner",
        "phone": null,
        "avatar": null,
        "total_predictions": 0,
        "correct_predictions": 0,
        "prediction_accuracy": 0,
        "learning_progress": {},
        "created_at": "...",
        "updated_at": "..."
      }
    }
  }
}
```

### Error response (400 Bad Request) – validation

```json
{
  "status": "error",
  "message": "Password must contain at least one number.",
  "errors": { "password": ["Password must contain at least one number."] }
}
```

### Error response (400) – duplicate email

```json
{
  "status": "error",
  "message": "A user with that email already exists."
}
```

Use the `access` token in the `Authorization` header for subsequent requests:  
`Authorization: Bearer <access>`.

---

## 2. Login

**POST** `/api/auth/login/`

Authenticates by email and password and returns JWT tokens.

### Headers

| Header          | Value              |
|-----------------|--------------------|
| `Content-Type`  | `application/json` |

### Request body (JSON)

| Field     | Type   | Required | Description |
|-----------|--------|----------|-------------|
| `email`   | string | Yes      | User email (case-insensitive) |
| `password`| string | Yes      | Password |

### Example request

```json
{
  "email": "john@example.com",
  "password": "SecurePass1"
}
```

### Success response (200 OK)

Same shape as register: `status`, `data.access`, `data.refresh`, `data.user`.

### Error response (401 Unauthorized)

```json
{
  "status": "error",
  "message": "Invalid credentials"
}
```

---

## 3. Profile (get / update)

**GET** `/api/auth/profile/` – get current user  
**PATCH** `/api/auth/profile/` – update current user

Requires authentication: `Authorization: Bearer <access>`.

### GET – Success (200)

```json
{
  "status": "success",
  "data": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile": { ... }
  }
}
```

### PATCH body (partial updates)

| Field       | Type   | Description |
|------------|--------|-------------|
| `username` | string | 3–30 chars, letters, numbers, underscores |
| `first_name` | string | |
| `last_name`  | string | |
| `email`    | string | |
| `profile`  | object | `risk_appetite`, `experience_level`, `phone` |

---

## 4. Logout

**POST** `/api/auth/logout/`

Blacklists the refresh token so it can no longer be used. Optional body:

```json
{ "refresh": "<refresh_token>" }
```

Requires: `Authorization: Bearer <access>`.

### Success (200)

```json
{
  "status": "success",
  "message": "Successfully logged out"
}
```

---

## 5. User stats

**GET** `/api/auth/stats/`

Returns high-level user stats. Requires: `Authorization: Bearer <access>`.

### Success (200)

```json
{
  "status": "success",
  "data": {
    "total_predictions": 0,
    "correct_predictions": 0,
    "prediction_accuracy": 0,
    "learning_progress": {},
    "risk_appetite": "moderate",
    "experience_level": "beginner"
  }
}
```

---

## 6. User activities

**GET** `/api/auth/activities/`

Returns recent activity for the current user. Requires: `Authorization: Bearer <access>`.

### Success (200)

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "activity_type": "login",
      "description": "User logged in",
      "metadata": {},
      "created_at": "2025-02-27T12:00:00Z"
    }
  ]
}
```

---

## 7. Wallet auth (Web3)

### Get sign-in nonce

**GET** `/api/auth/wallet/nonce/?address=0xYourEthereumAddress`

Returns a one-time message to sign with the wallet. Nonce is valid for 5 minutes.

### Success (200)

```json
{
  "status": "success",
  "data": { "nonce": "FinanceAI sign-in: <random_hex>" }
}
```

### Verify signature and login

**POST** `/api/auth/wallet/verify/`

Body:

```json
{
  "address": "0x...",
  "signature": "0x..."
}
```

On success, returns the same token envelope as login (`access`, `refresh`, `user`). If the wallet is new, a user is created and linked to the address.

---

## Postman

Import the collection:

- **File:** `postman/FinanceAI_Auth.postman_collection.json`

Set the collection variable `base_url` (e.g. `http://localhost:8000`). After running **Register** or **Login**, use the **Tests** script to save `access` and `refresh` into collection variables so **Profile**, **Logout**, etc. use the token automatically.

---

## Frontend flow

1. **Register:** `POST /api/auth/register/` with name, email, password, risk_appetite, experience_level → store `data.access`, `data.refresh`, `data.user` (e.g. in `localStorage`) → redirect to dashboard.
2. **Login:** `POST /api/auth/login/` with email, password → same storage and redirect.
3. **Authenticated requests:** Send `Authorization: Bearer <access>` on each request. On 401, clear tokens and redirect to login.
4. **Refresh (optional):** Use `POST /api/token/refresh/` with `{"refresh": "<refresh>"}` to get a new `access` token when it expires.

All auth endpoints return JSON only; errors use `status: "error"` and a `message` field for a smooth, consistent flow.
