## -----------  builder  -----------
FROM python:3.12-slim AS builder

WORKDIR /build

RUN python -m venv /opt/venv

# Install dependencies first (cached until pyproject.toml changes)
COPY pyproject.toml ./
RUN mkdir -p app && touch app/__init__.py \
    && /opt/venv/bin/pip install --no-cache-dir .

# Copy source and reinstall package only (deps already cached)
COPY . .
RUN /opt/venv/bin/pip install --no-cache-dir --no-deps .

## -----------  runtime  -----------
FROM python:3.12-slim AS runtime

RUN groupadd --system appuser && useradd --system --gid appuser appuser

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /build/alembic /app/alembic
COPY --from=builder /build/alembic.ini /app/alembic.ini
COPY --from=builder /build/app /app/app

ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app

USER appuser

EXPOSE 5060

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5060"]
