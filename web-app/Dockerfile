FROM python:3.10-slim-bookworm AS dependencies

ENV PIPENV_VENV_IN_PROJECT=1

WORKDIR /app

COPY Pipfile Pipfile.lock ./
RUN python -m pip install --no-cache-dir pipenv==2024.4.1 \
    && pipenv verify \
    && pipenv sync

FROM python:3.10-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

COPY --from=dependencies /app/.venv /app/.venv
COPY app.py ./
COPY templates/ ./templates/
COPY static/ ./static/

USER 10001:10001

EXPOSE 5000

STOPSIGNAL SIGINT

CMD ["python", "-m", "flask", "--app", "app", "--no-debug", "run", "--host", "0.0.0.0", "--port", "5000"]
