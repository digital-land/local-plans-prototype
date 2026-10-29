# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FLASK_APP=application.wsgi:app \
    FLASK_CONFIG=config.Config \
    PORT=5050

WORKDIR /code

# Install dependencies first so this layer is cached between code changes
COPY requirements/requirements.txt requirements/requirements.txt
RUN pip install -r requirements/requirements.txt \
    && pip uninstall -y pip

RUN useradd --system --uid 10001 --no-create-home app

COPY --chown=root:root . .

USER app
EXPOSE 5050

ENTRYPOINT ["./docker-entrypoint.sh"]
