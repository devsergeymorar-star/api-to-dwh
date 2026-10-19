# Build from the repository root:
#   docker build -f dbt/Dockerfile -t dbt-runner .
FROM python:3.12-slim

RUN pip install --no-cache-dir "dbt-core==1.12.6" "dbt-clickhouse==1.10.3" \
 && useradd --create-home --uid 1000 app \
 && install -d -o app /dbt

WORKDIR /dbt
COPY --chown=app dbt/ ./
ENV DBT_PROFILES_DIR=/dbt \
    DBT_SEND_ANONYMOUS_USAGE_STATS=false \
    PYTHONUNBUFFERED=1
USER app
ENTRYPOINT ["dbt"]
CMD ["build"]
