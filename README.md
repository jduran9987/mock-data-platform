# Mock Data Platform

Simulated e-commerce data platform for practicing data infrastructure, architecture, patterns, and tooling. Built entirely on open-source tools. Upstream sources deliberately produce messy data — late-arriving events, schema drift, duplicates, nulls in unexpected places, and out-of-order records — so downstream layers must handle real-world problems at every stage.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Upstream Sources                             │
│                                                                     │
│   Third-Party APIs          CDC / Snapshots         Event Streams   │
│   (payments, shipping,      (application DB         (clickstream,   │
│    marketing)                change data capture)    inventory,      │
│                                                      transactions)  │
└──────────┬──────────────────────┬──────────────────────┬────────────┘
           │                      │                      │
           ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Ingestion                                  │
│                                                                     │
│          Streaming (Kafka / Flink)      Batch (Spark / Airflow)     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Storage                                    │
│                                                                     │
│              Data Lake (Iceberg / S3)     Warehouse                 │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Processing                                   │
│                                                                     │
│        Stream (real-time aggregations)    Batch (historical loads)  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Transformation                                │
│                                                                     │
│              dbt (star schema + OBT models)                         │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Presentation                                 │
│                                                                     │
│                      BI / Analytics                                 │
└─────────────────────────────────────────────────────────────────────┘

Cross-cutting: Observability (data quality, pipeline health, SLAs)
               Governance (lineage, metadata catalog, access policies)
```

## What Exists Today

The platform is under active development. Currently implemented:

- **Payments Vendor API** (`sources/apis/payments-vendor/`) — A Stripe-compatible REST API that simulates a third-party payment processor. Generates customer records with configurable messy data and data quality issues. Backed by PostgreSQL.

All other layers (ingestion, storage, processing, transformation, serving, observability, governance) are planned but not yet built.

## Project Structure

```
mock-data-platform/
├── docker-compose.yml          # All platform services
├── sources/                    # Simulated upstream data generators
│   ├── apis/                   # Third-party API simulators
│   │   └── payments-vendor/    # Stripe-compatible payments API ✓
│   ├── cdc/                    # Application database CDC and snapshots
│   └── events/                 # Event stream producers
├── ingestion/                  # Pipeline definitions
│   ├── streaming/              # Kafka consumers, Flink jobs
│   └── batch/                  # Spark jobs, Airflow DAGs
├── storage/                    # Storage layer configs (Iceberg, S3)
├── processing/                 # Stream and batch processing jobs
├── transform/                  # dbt project
├── serving/                    # Presentation / BI layer
├── observability/              # Monitoring, alerting, data quality
├── governance/                 # Lineage, catalog, access policies
└── infra/                      # Infrastructure as code (Terraform)
```

## Data Domain

The platform models an e-commerce business generating customers, orders, products, inventory, payments, shipments, returns, clickstream events, and marketing campaign interactions. Data flows from upstream sources through ingestion into storage, where it is processed, transformed into analytical models, and served for BI consumption.

## Running

```bash
docker compose up -d              # Start all services
docker compose up -d <service>    # Start a single service
docker compose down               # Stop all services
docker compose logs -f <service>  # Tail service logs
docker compose ps                 # Check service status
```

## Services

| Service | Port | Description |
|---|---|---|
| `payments-vendor-api` | 8010 | Stripe-compatible payments API |
| `payments-vendor-db` | 5433 | PostgreSQL backing the payments API |
