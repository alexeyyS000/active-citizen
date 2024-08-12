ARG PYTHON_VERSION

FROM python:${PYTHON_VERSION:-3.10}-slim-buster as build

ARG POETRY_VERSION

ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_NO_CACHE_DIR=off
ENV PYTHONDONTWRITEBYTECODE=on
ENV PYTHONFAULTHANDLER=on
ENV PYTHONUNBUFFERED=on
ENV PIP_DEFAULT_TIMEOUT=100
ENV POETRY_VERSION=${POETRY_VERSION}

RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc curl

WORKDIR /app

RUN pip install poetry==${POETRY_VERSION}

RUN python -m venv .venv

COPY pyproject.toml .
COPY poetry.lock .

RUN poetry export --format=requirements.txt --without=dev | .venv/bin/pip install -r /dev/stdin

# Compile locales for email domain
COPY src/locale locale
RUN .venv/bin/pybabel compile --domain=messages --use-fuzzy --directory=locale

FROM python:${PYTHON_VERSION:-3.10}-slim

WORKDIR /app

# Install curl for healthchecking
RUN apt-get -y update && apt-get install -y --no-install-recommends curl jq

RUN groupadd -g 999 python && \
    useradd -r -u 999 -g python python
USER 999

# Copy installed packages
COPY --from=build /app/.venv .venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy compiled locales
COPY --from=build /app/locale locale

# Copy application
COPY src .
