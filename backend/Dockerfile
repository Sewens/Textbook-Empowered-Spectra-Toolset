FROM python:3.13-slim AS runtime
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.11.1 /uv /usr/local/bin/uv
COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev
COPY backend/app ./app
COPY raw_data /raw_data
ENV RELEASE_PATH=/raw_data/basic_groups_v07_20260619
ENV DOCS_SUMMARY_PATH=/raw_data/docs/ir_ie_v07_core_data_model_v20260622.summary.json
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
