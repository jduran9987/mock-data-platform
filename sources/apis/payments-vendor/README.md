# Payments Vendor API

Stripe-compatible payments API that simulates a third-party payment processor. This is an upstream data source for the mock-data-platform's ingestion pipelines.

## Endpoints

### `GET /v1/customers`

Returns a paginated list of customers, sorted by creation date (newest first).

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | 10 | Number of customers to return (1-100) |
| `starting_after` | string | — | Cursor for forward pagination (customer ID) |
| `ending_before` | string | — | Cursor for backward pagination (customer ID) |
| `email` | string | — | Filter by exact email match |

### `GET /v1/customers/{customer_id}`

Retrieves a single customer by ID.

**Error (404):**

```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "No such customer: cus_xxx",
    "param": "id",
    "code": "resource_missing"
  }
}
```

## Field Reference

### Customer Object

| Field | Type | Nullable | Required | Notes |
|---|---|---|---|---|
| `id` | string | No | Yes | Stripe-style ID with `cus_` prefix |
| `object` | string | No | Yes | Always `"customer"` |
| `address` | object | Yes | No | Nested address object; may be omitted entirely |
| `balance` | integer | No | Yes | Account balance in cents |
| `created` | integer | No | Yes | Unix timestamp (seconds) |
| `currency` | string | Yes | No | ISO currency code (e.g., `"usd"`, `"eur"`, `"gbp"`, `"cad"`) |
| `default_source` | string | Yes | No | Payment method ID with `card_` prefix |
| `delinquent` | boolean | No | Yes | Account delinquency status |
| `description` | string | Yes | No | Arbitrary text description |
| `email` | string | Yes | No | Customer email address |
| `invoice_prefix` | string | No | Yes | 8-character alphanumeric code |
| `livemode` | boolean | No | Yes | Always `false` |
| `metadata` | object | No | Yes | Key-value pairs; defaults to `{}` |
| `name` | string | Yes | No | Customer full name |
| `phone` | string | Yes | No | Phone number |
| `shipping` | object | Yes | No | Nested shipping object; may be omitted entirely |
| `tax_exempt` | string | No | Yes | One of: `"none"`, `"exempt"`, `"reverse"` |

### Address Object (nested in `address` and `shipping.address`)

| Field | Type | Nullable | Required |
|---|---|---|---|
| `city` | string | Yes | No |
| `country` | string | Yes | No |
| `line1` | string | Yes | No |
| `line2` | string | Yes | No |
| `postal_code` | string | Yes | No |
| `state` | string | Yes | No |

### Shipping Object (nested in `shipping`)

| Field | Type | Nullable | Required |
|---|---|---|---|
| `address` | object | Yes | No |
| `name` | string | Yes | No |
| `phone` | string | Yes | No |

### List Response Wrapper

| Field | Type | Nullable | Required | Notes |
|---|---|---|---|---|
| `object` | string | No | Yes | Always `"list"` |
| `url` | string | No | Yes | Always `"/v1/customers"` |
| `has_more` | boolean | No | Yes | Whether additional pages exist |
| `data` | array | No | Yes | Array of customer objects |
| `request_id` | string | No | Yes | Unique request identifier for tracking |

### Response Example

```json
{
  "object": "list",
  "url": "/v1/customers",
  "has_more": false,
  "request_id": "req_abc123...",
  "data": [
    {
      "id": "cus_abc123...",
      "object": "customer",
      "address": {
        "city": "San Francisco",
        "country": "US",
        "line1": "123 Market St",
        "line2": null,
        "postal_code": "94105",
        "state": "CA"
      },
      "balance": 0,
      "created": 1710500000,
      "currency": "usd",
      "default_source": "card_abc123...",
      "delinquent": false,
      "description": "Example customer",
      "email": "jane@example.com",
      "invoice_prefix": "ABC12345",
      "livemode": false,
      "metadata": {},
      "name": "Jane Doe",
      "phone": "+14155551234",
      "shipping": {
        "address": {
          "city": "San Francisco",
          "country": "US",
          "line1": "123 Market St",
          "line2": null,
          "postal_code": "94105",
          "state": "CA"
        },
        "name": "Jane Doe",
        "phone": "+14155551234"
      },
      "tax_exempt": "none"
    }
  ]
}
```

---

## Internal Development

### Data Simulation Overview

Every `GET /v1/customers` request triggers the data generation engine before returning results. The engine creates new customer records, mutates existing ones, and probabilistically injects data quality issues — simulating the kind of messy data a real third-party API produces over time.

### New and Updated Records

Each request generates **1–5 new customers** and **0–3 updates to existing customers**. These ranges are controlled by `SimulationConfig` in `internal/config.py`.

**New records** are fully generated with randomized data via Faker. The `created` timestamp is set to the current time minus a random offset of 0–365 days, simulating accounts of varying ages.

**Updated records** are selected randomly from the existing customer pool. The following fields are re-randomized on update: `name`, `phone`, `description`, `balance`, `delinquent`, and `metadata`. Other fields like `id`, `email`, `created`, and `currency` are not mutated.

There is no explicit `updated_at` timestamp or version field — this is intentional. Downstream consumers must detect changes by comparing consecutive fetches, which mirrors how many real vendor APIs behave.

### Messy Data Simulation

The API injects messiness at two levels: **field-level nulls** and **missing nested objects**.

**Nullable fields** (`name`, `email`, `phone`, `description`, `currency`, `default_source`, and all address/shipping sub-fields) are randomly set to `null` at a **25% rate** via `maybe_null()` in `internal/messy.py`. This rate is controlled by `nullable_field_null_rate` in the config.

**Optional nested objects** (`address` and `shipping`) are omitted entirely at a **10% rate** via `maybe_omit_nested()`. When omitted, the field is absent from the response rather than being set to `null`. This rate is controlled by `optional_nested_missing_rate` in the config.

Additional randomization in field values:
- `balance`: 75% chance of `0`, 25% chance of a random value between `-10000` and `50000` cents
- `delinquent`: 5% chance of `true`
- `tax_exempt`: 75% `"none"`, 12.5% `"exempt"`, 12.5% `"reverse"`
- `metadata`: random word pairs; 25% chance of empty `{}`

### Data Quality Issues

Beyond general messiness, the API injects specific **contract violations** that represent real data quality problems. These are tracked in an in-memory `DQIssueRegistry` and can be resolved via the internal fix endpoint.

**`null_email_on_required`** — At a **2% rate**, a newly created customer has its `email` set to `null` after generation. The original email value is preserved in the issue registry. In a real Stripe-like API, email is effectively required, so this simulates a contract violation that downstream systems must handle.

**`duplicate_id`** — At a **2% rate**, an existing customer is duplicated in the list response. The same customer object appears twice in the `data` array with identical IDs. This simulates a serialization-layer bug that produces duplicate records.

Both issue rates are controlled by the `dq_issue_rate` config parameter.

### Fixing Data Quality Issues

Every API response includes a `request_id` (in both the response body and the `Request-Id` header). When a DQ issue is injected, it is recorded against that request ID.

Use the internal fix endpoint to resolve issues for a given request:

```
POST /internal/fix-data-quality-issues
```

**Request:**

```json
{
  "request_id": "req_abc123..."
}
```

**Response:**

```json
{
  "request_id": "req_abc123...",
  "issues_resolved": 2,
  "details": [
    {
      "resource_type": "customer",
      "resource_id": "cus_xyz...",
      "issue_type": "null_email_on_required",
      "resolved": true
    },
    {
      "resource_type": "customer",
      "resource_id": "cus_abc...",
      "issue_type": "duplicate_id",
      "resolved": true
    }
  ]
}
```

**How it works:**

- For `null_email_on_required` issues, the fix endpoint restores the original email value in the database. Subsequent reads of that customer will return the correct email.
- For `duplicate_id` issues, the issue is marked as resolved in the registry, but since duplication is injected at the serialization layer (not persisted), no database change is needed — the duplicate will not appear in future responses.

**Limitations:**

- The issue registry is **in-memory only** — all tracked issues are lost on service restart.
- Issues can only be resolved by `request_id`, not by individual customer ID or issue type.

### Configuration Reference

All simulation parameters live in `internal/config.py` as a `SimulationConfig` dataclass:

| Parameter | Default | Description |
|---|---|---|
| `min_new_records` | 1 | Minimum new customers created per request |
| `max_new_records` | 5 | Maximum new customers created per request |
| `min_updated_records` | 0 | Minimum existing customers mutated per request |
| `max_updated_records` | 3 | Maximum existing customers mutated per request |
| `nullable_field_null_rate` | 0.25 | Probability a nullable field is set to `null` |
| `optional_nested_missing_rate` | 0.10 | Probability an optional nested object is omitted |
| `dq_issue_rate` | 0.02 | Probability of injecting a DQ issue per eligible check |
| `default_page_size` | 10 | Default number of records per page |
| `max_page_size` | 100 | Maximum allowed page size |

## Running

```bash
# From project root
docker compose up -d payments-vendor-api

# Locally (requires PostgreSQL)
cd sources/apis/payments-vendor
DATABASE_URL=postgresql://payments:payments@localhost:5433/payments_vendor uv run payments-vendor
```
