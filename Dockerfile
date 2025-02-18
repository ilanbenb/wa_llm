FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

RUN apt-get update -qy
RUN apt-get install -qyy -o APT::Install-Recommends=false -o APT::Install-Suggests=false ca-certificates \
    git wget

WORKDIR /app

RUN --mount=type=secret,id=netrc,target=/root/.netrc,mode=0600 \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=./uv.lock,target=uv.lock \
    --mount=type=bind,source=./pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=./.python-version,target=.python-version \
    uv sync --frozen --no-dev --no-install-project

COPY . /app

FROM python:3.11-slim

COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:${PYTHONPATH:-}"

WORKDIR /app

# Install cron
RUN apt-get update && apt-get install -y cron

# Create the cron job file
RUN echo "0 0 * * * /usr/local/bin/python /src/daily_ingest/daily_ingest.py >> /var/log/cron.log 2>&1" > /etc/cron.d/ingest-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/ingest-cron

# Apply cron job
RUN crontab /etc/cron.d/ingest-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the cron service as the main process
CMD cron && tail -f /var/log/cron.log

CMD ["python", "app/main.py"]