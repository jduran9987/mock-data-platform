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

**Response:**

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

### `GET /v1/customers/{customer_id}`

Retrieves a single customer by ID.

**Response:** A single customer object (same shape as above, without the list wrapper).

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

## Field Nullability

The following fields are nullable and may return `null` on any given record:

`name`, `email` (see note), `phone`, `description`, `currency`, `default_source`, `address`, `shipping`

Optional nested objects (`address`, `shipping`) may be omitted entirely.

## Running

```bash
# From project root
docker compose up -d payments-vendor-api

# Locally (requires PostgreSQL)
cd sources/apis/payments-vendor
DATABASE_URL=postgresql://payments:payments@localhost:5433/payments_vendor uv run payments-vendor
```
