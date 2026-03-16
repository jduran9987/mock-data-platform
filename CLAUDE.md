# mock-data-platform
 
Simulated e-commerce data platform for practicing data infrastructure, architecture, patterns, and tooling. Built entirely on open-source tools. Over-indexes on ingestion, storage, stream/batch processing, and performance.
 
## Architecture
 
The platform simulates a full e-commerce business with messy, real-world data across these layers:
 
- **Upstream Sources**: Simulated third-party APIs (payments, shipping, marketing), application database CDC and snapshots, event streaming (clickstream, inventory, transactions)
- **Ingestion**: Streaming pipelines (Kafka/Flink) and batch pipelines (Spark/Airflow)
- **Storage**: Data lake (Iceberg/MinIO) and warehouse layers
- **Processing**: Stream processing for real-time aggregations, batch processing for historical loads
- **Transformation**: dbt for star schema and OBT (One Big Table) modeling
- **Presentation**: BI/analytics serving layer
- **Observability**: Data quality monitoring, pipeline health, SLAs
- **Governance**: Lineage tracking, metadata catalog, access policies
 
## Project Structure
 
```
mock-data-platform/
├── CLAUDE.md
├── docker-compose.yml          # All platform components (eventual k8s migration)
├── infra/                      # Infrastructure as code (Terraform/Pulumi)
├── sources/                    # Simulated upstream data generators
│   ├── apis/                   # Third-party API simulators (payments, shipping, marketing)
│   ├── cdc/                    # Application database CDC and snapshot generators
│   └── events/                 # Event stream producers (clickstream, inventory, transactions)
├── ingestion/                  # Pipeline definitions
│   ├── streaming/              # Kafka consumers, Flink jobs
│   └── batch/                  # Spark jobs, Airflow DAGs
├── storage/                    # Storage layer configs (Iceberg, MinIO)
├── processing/                 # Stream and batch processing jobs
├── transform/                  # dbt project (star schema + OBT models)
├── serving/                    # Presentation/BI layer
├── observability/              # Monitoring, alerting, data quality checks
├── governance/                 # Lineage, catalog, access policies
└── .claude/
    └── skills/                 # Area-specific skills (loaded on demand)
```
 
## Tech Stack
 
Most components are open source. Specific tools will be chosen as each layer is built, but the general direction:
 
- **Orchestration**: Apache Airflow
- **Streaming**: Apache Kafka, Apache Flink
- **Batch Processing**: Apache Spark
- **Storage**: Apache Iceberg, S3 
- **Transformation**: dbt
- **Observability**: Great Expectations, Prometheus/Grafana
- **Governance**: OpenLineage, DataHub or OpenMetadata
- **IaC**: Terraform
- **Containers**: Docker Compose (migrating to Kubernetes)
- **Project Managers**: UV
 
## Commands
 
```bash
docker compose up -d              # Start full platform
docker compose up -d <service>    # Start individual service
docker compose down               # Stop all services
docker compose logs -f <service>  # Tail service logs
docker compose ps                 # Check service status
```
 
## Data Domain
 
E-commerce business generating:
 
- Customers, orders, products, inventory, payments, shipments, returns
- Clickstream and session events
- Marketing campaign interactions (email, ads, attribution)
- Third-party data from payment processors, shipping carriers, marketing platforms
 
Upstream sources deliberately produce messy data: late-arriving events, schema drift, duplicates, nulls in unexpected places, out-of-order records, and volumes large enough to surface big data problems.
 
## Conventions
 
- Every component runs in Docker; nothing requires host-installed runtimes
- Use uv for Python project management (see **UV Project Setup** below)
- docker-compose.yml at project root is the single entrypoint for the platform
- Each top-level directory owns its own README explaining its purpose and usage
- New services must be added to docker-compose.yml with health checks
- Data generators should be configurable for volume, error rate, and schema evolution
- Processing jobs should have both unit tests and integration tests against containerized infrastructure
- Use `.claude/skills/` for area-specific instructions (e.g., building API simulators, writing Flink jobs) — these load on demand when working in that area
 
## Modeling
 
- Star schema models for analytical queries (facts + dimensions)
- OBT models for simplified downstream consumption
- All models defined in dbt with tests and documentation
- Slowly changing dimensions (SCD Type 2) for historical tracking
 
## UV Project Setup

When creating a new Python project, follow these steps:

1. **Initialize as a packaged application** using the src layout:
   ```bash
   uv init --python 3.14 --package <name>
   ```
   This produces the recommended directory structure:
   ```
   <name>/
   ├── .python-version
   ├── README.md
   ├── pyproject.toml
   └── src/
       └── <name_underscored>/
           └── __init__.py
   ```

2. **Remove the `.git` directory** that `uv init` creates — the monorepo root manages version control:
   ```bash
   rm -rf <name>/.git
   ```

3. **Use the `uv_build` backend** — this is already configured by `--package`, but verify `pyproject.toml` contains:
   ```toml
   [build-system]
   requires = ["uv_build>=0.10.9,<0.11.0"]
   build-backend = "uv_build"
   ```

4. Place application code under `src/<package_name>/` following the src layout. The module name is the project name with dashes replaced by underscores (e.g., `payments-vendor` → `src/payments_vendor/`).

## Python Code Standards

All Python files must follow these standards:

- **Docstrings**: Every module, class, and function/method must have a brief docstring. Use Google-style docstrings. Keep them concise — one line for simple items, a short paragraph + `Args:`/`Returns:` sections for more complex ones.
- **Type annotations**: All function arguments and return values must be annotated. Annotate variables where the type isn't obvious from the assignment (e.g., empty collections, `None` initializations, or complex expressions).
- **Ruff compliance**: All code must pass `ruff check` and `ruff format`. Follow ruff defaults — this includes import sorting (isort-compatible), PEP 8 style, and common lint rules.

## Key Design Principles
 
- Simulate real production problems: backpressure, data skew, late arrivals, schema evolution
- Prefer idempotent, replayable pipelines
- Every pipeline should have observability from day one
- Storage format choices should optimize for the query patterns they serve
- Infrastructure as code for everything — no manual configuration
