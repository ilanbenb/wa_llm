FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
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

FROM python:3.12-slim-bookworm

COPY --from=builder --chown=app:app /app /app
COPY --from=aldinokemal2104/go-whatsapp-web-multidevice:latest /app/whatsapp /app/whatsapp

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Presuming there is a `my_app` command provided by the project
CMD ["python", "src/main.py"]