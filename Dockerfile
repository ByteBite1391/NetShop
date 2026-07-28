# NexCart production Dockerfile — multi-stage for small final image.
#
# Stage 1 (builder): install dependencies into a venv.
# Stage 2 (runtime): copy the venv + source into a slim image, run as non-root.
#
# Why multi-stage? The build stage carries gcc + dev headers needed to compile
# psycopg2 and Pillow; the runtime stage doesn't, which shrinks the image and
# reduces attack surface.

# ---------- builder ----------
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Build deps for psycopg2 + Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY requirements/ ./requirements/
RUN pip install --upgrade pip && pip install -r requirements/prod.txt

# ---------- runtime ----------
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.production

# Runtime libs for psycopg2 + Pillow (no headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r nexcart && useradd -r -g nexcart -d /app nexcart

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=nexcart:nexcart . .

RUN mkdir -p /app/staticfiles /app/media && chown -R nexcart:nexcart /app

USER nexcart

EXPOSE 8000

# Gunicorn with Uvicorn-compatible worker class. Tune workers in compose.
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
