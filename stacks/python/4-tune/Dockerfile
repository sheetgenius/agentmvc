FROM python:3.14.7-slim-bookworm@sha256:82bc3c539b8813ada9d68c63b40158fa002f7f33de9bf3312a3dfdc0620dff56 AS builder
RUN pip install --no-cache-dir uv==0.12.20
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache --compile-bytecode

FROM python:3.14.7-slim-bookworm@sha256:82bc3c539b8813ada9d68c63b40158fa002f7f33de9bf3312a3dfdc0620dff56
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY conduit ./conduit
COPY config ./config
COPY manage.py ./
COPY bin/serve ./bin/serve
RUN python -m compileall -q conduit config manage.py && useradd --create-home --uid 10001 app
USER app
CMD ["./bin/serve"]
