## -----------  builder  -----------
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir .

COPY . .
RUN /opt/venv/bin/pip install --no-cache-dir .

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
