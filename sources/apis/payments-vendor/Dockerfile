FROM python:3.14-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock README.md ./
COPY src/payments_vendor/__init__.py src/payments_vendor/__init__.py
RUN uv sync --frozen --no-dev

COPY src/ src/

EXPOSE 8000

CMD ["uv", "run", "payments-vendor"]
