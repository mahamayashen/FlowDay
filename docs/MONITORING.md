# FlowDay Monitoring

## Overview

FlowDay exposes a Prometheus-compatible `/metrics` endpoint and ships Grafana dashboards for observability. The stack includes:

- **Prometheus** — scrapes `/metrics` from the backend every 15 s
- **Grafana** — auto-provisions the Prometheus datasource and the FlowDay dashboard at startup
- **Custom AI metrics** — placeholder Histogram/Counter collectors for the agent pipeline (recorded in `backend/app/core/metrics.py`)

## Local Setup

1. Start the full stack (includes Prometheus + Grafana):
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```

2. Start the backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 5060
   ```

3. Access:
   | Service    | URL                        | Default credentials |
   |------------|---------------------------|---------------------|
   | Grafana    | http://localhost:3001      | admin / admin       |
   | Prometheus | http://localhost:9090      | —                   |
   | Metrics    | http://localhost:5060/metrics | —                |

4. The **FlowDay Overview** dashboard is auto-provisioned — open Grafana, navigate to Dashboards → FlowDay Overview.

## Disabling Prometheus

Set `PROMETHEUS_ENABLED=false` in `.env` to disable the `/metrics` endpoint (e.g., in production environments where a different scraper is used).

## Available Metrics

### HTTP metrics (auto-instrumented)

| Metric | Type | Description |
|--------|------|-------------|
| `http_request_duration_seconds` | Histogram | Request latency by method, path, status |
| `http_requests_total` | Counter | Total requests by method, path, status |

### AI agent metrics (placeholders)

These are defined in `backend/app/core/metrics.py`. Agent code will call them when the agent pipeline is implemented.

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `agent_latency_seconds` | Histogram | `agent_name` | Time spent in an AI agent call |
| `token_cost_total` | Counter | `agent_name`, `model` | Cumulative token cost |
| `judge_score` | Histogram | `agent_name` | Judge agent score (0–100) |

## Dashboard Panels

| Panel | PromQL summary |
|-------|---------------|
| Request Latency (p50/p95/p99) | `histogram_quantile` on `http_request_duration_seconds_bucket` |
| Error Rate (5xx) | ratio of 5xx to total requests |
| Active Users | placeholder using total request count |
| Agent Latency p95 | `histogram_quantile` on `agent_latency_seconds_bucket` |
| Token Cost Rate | `rate(token_cost_total)` by agent + model |
| Judge Score Distribution | `histogram_quantile` on `judge_score_bucket` |

## Adding New Metrics

1. Define a module-level singleton in `backend/app/core/metrics.py`:
   ```python
   my_metric: Counter = Counter("my_metric_total", "Description", labelnames=["label"])
   ```
2. Call it from service or agent code:
   ```python
   from app.core.metrics import my_metric
   my_metric.labels(label="value").inc()
   ```
3. The metric will automatically appear at `/metrics` and in Grafana.
