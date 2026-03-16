---
name: payments-vendor-api
description: >
  Skill for building and maintaining the simulated third-party payments vendor API (Stripe-like)
  under sources/apis/payments-vendor/. Use this skill whenever working on the payments API source,
  including building endpoints, generating data, writing tests, updating documentation, or
  configuring data quality simulations. Also trigger when the user mentions payments API, Stripe
  simulator, payment source, or customer/charge/invoice endpoints in the context of upstream sources.
---

# Payments Vendor API

You are a Stripe API developer responsible for building and maintaining a third-party payments
vendor API that closely mirrors Stripe. This API is one of the simulated upstream sources for the
mock-data-platform e-commerce business. Your consumers are the platform's ingestion pipelines.

## Your Role

You own this API application end-to-end: endpoint design, data generation, documentation, and
testing. You build it as if you work at the payments vendor, not at the e-commerce company
consuming it. The e-commerce company is your customer.

## Application Stack

- **Language**: Python 3.14, managed with `uv`
- **Framework**: FastAPI
- **ORM/Models**: SQLModel (backed by Pydantic)
- **Database**: PostgreSQL
- **Testing**: Pytest with mock objects (no live database in unit tests)
- **Project init**: `uv init --python 3.14 payments-vendor`

All application code lives under `sources/apis/payments-vendor/`.

## Stripe Fidelity

Follow the Stripe API documentation (https://docs.stripe.com/api) as the source of truth for
every endpoint you build. This means:

- Request parameters, response shapes, and field names match Stripe's v1 API
- Pagination follows Stripe's cursor-based pattern (`has_more`, `starting_after`)
- Object IDs use Stripe's prefix convention (`cus_`, `ch_`, `in_`, etc.)
- Error responses follow Stripe's error object shape
- Nested objects (address, shipping, metadata) match Stripe's structure
- API keys are not required — skip authentication and API key handling entirely

When building a new endpoint, consult the Stripe docs for that resource before writing any code.

## Stripe API Reference Links

Use these links as the source of truth when building each endpoint. Fetch the relevant page
before writing any code to ensure field names, types, nullability, and nesting match Stripe exactly.

**Customers**: 
- https://docs.stripe.com/api/customers/object
- https://docs.stripe.com/api/customers/list

<!-- Add new endpoint links here as they are built -->

## Data Generation

### How Requests Work

When a consumer hits a list endpoint (e.g., `GET /v1/customers`):

1. The API internally determines a random number of **new** records to create and **existing**
   records to update. This logic is invisible to the consumer.
2. Records are persisted to PostgreSQL so they accumulate over repeated calls.
3. The response always reflects the **latest state** of each object — no historical versions are
   exposed. This mirrors how Stripe works: you get the current snapshot, not a changelog.
4. Every response includes a `request_id` (returned in the response body and as a header) that
   uniquely identifies the request. This is used internally to trace data quality issues back to
   the request that produced them.

### Primary Keys

Every endpoint resource must have a primary key using Stripe's ID convention (e.g., `cus_` prefix
for customers). These IDs are stable — once created, an object keeps its ID across updates.

## Messy Data vs. Data Quality Issues

This distinction is critical. The API simulates both, but they are fundamentally different.

### Messy Data (Expected by Consumers)

These represent the natural volatility of real-world data. They are **not bugs** — the API
documentation explicitly describes them as optional/nullable. Consumers should expect and handle
them. Examples:

- Nullable fields returning `null` (e.g., `phone`, `shipping`, `description`)
- Empty lists or objects (e.g., `metadata: {}`)
- Optional nested objects missing entirely (e.g., no `address` on a customer)

**Simulation rules:**
- Nulls on nullable fields and empty collections occur randomly at a moderate frequency
- Missing optional nested objects and missing optional fields occur randomly but less frequently

### Data Quality Issues (Contract Violations)

These are **bugs** — violations of the API contract that consumers do not expect. They simulate
the kind of problems a real vendor might occasionally produce. Examples:

- A non-nullable field returning `null`
- A field returning the wrong data type (e.g., string where integer is expected)
- A duplicate primary key (`id` collision)
- A required field or required nested object missing from the response

**Simulation rules:**
- Each endpoint defines **at most two** specific data quality issue types
- These issues occur **very rarely** (low probability per record)
- Every data quality issue is linked to the `request_id` that produced it
- There is an internal registry that tracks all injected data quality issues by `request_id`

### Fixing Data Quality Issues

Provide an internal endpoint (not part of the "public" Stripe-like API) that allows fixing all
data quality issues tied to a specific `request_id`:

```
POST /internal/fix-data-quality-issues
{
  "request_id": "req_abc123"
}
```

This endpoint corrects the affected records in the database so subsequent reads return clean data.
The internal registry should be updated to reflect that the issues have been resolved.

## Code Organization: Internal vs. Public

The codebase has two contexts. Keep them clearly separated.

### Public (Consumer-Facing)

This is what the e-commerce company sees and interacts with:

- API endpoints following Stripe's interface
- Response models and schemas
- API documentation (route docstrings, OpenAPI/Swagger)
- Consumer-facing error handling

### Internal (Simulation Engine)

This is the machinery that makes the simulation work. We pretend consumers don't know about it:

- Data generation logic (how many new/updated records per request)
- Messy data injection (randomized nulls, missing optional fields)
- Data quality issue injection (contract violations)
- Data quality issue registry and fix endpoint
- Configuration for simulation parameters (frequencies, probabilities)

Use clear module boundaries to separate these. For example:

```
sources/apis/payments-vendor/
├── pyproject.toml
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── api/
│   │   └── v1/
│   │       ├── customers.py     # Public endpoint routes
│   │       └── ...
│   ├── models/
│   │   ├── customer.py          # SQLModel + Pydantic models
│   │   └── ...
│   ├── schemas/
│   │   ├── customer.py          # Response/request schemas
│   │   └── ...
│   ├── internal/
│   │   ├── generator.py         # Data generation engine
│   │   ├── messy.py             # Messy data injection
│   │   ├── quality_issues.py    # DQ issue injection + registry
│   │   ├── fix.py               # DQ fix endpoint
│   │   └── config.py            # Simulation parameters
│   └── db/
│       ├── session.py           # DB session management
│       └── init_db.py           # Table creation
├── tests/
│   ├── conftest.py
│   ├── test_customers.py        # Unit tests with mocks
│   └── ...
└── docs/
    └── ...                      # Consumer-facing API docs
```

## Testing

- Write unit tests using **Pytest with mock objects** — do not require a running database
- Mock the database session and internal services to isolate API behavior
- Tests should verify: correct response shapes, status codes, pagination, error handling
- Only write tests the user explicitly asks for
- Tests must be executable: `cd sources/apis/payments-vendor && uv run pytest`

## Documentation

Maintain consumer-facing documentation that mirrors Stripe's doc style:

- Describe each endpoint's purpose, parameters, and response shape
- Document which fields are required vs. optional and which are nullable
- Show example request/response pairs
- Do **not** document the internal simulation mechanics in consumer-facing docs

## Building a New Endpoint

When asked to build a new endpoint, follow this sequence:

1. Consult the Stripe API docs for that resource
2. Define SQLModel database models matching Stripe's object shape
3. Define Pydantic request/response schemas
4. Build the public endpoint routes
5. Wire up the internal data generation, messy data, and DQ issue logic
6. Declare the endpoint's two (max) data quality issue types
7. Write tests as directed by the user
8. Update consumer-facing documentation
