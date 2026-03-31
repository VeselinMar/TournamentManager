FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && \
    apt-get install -y build-essential libpq-dev libssl-dev libffi-dev curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/* &&\
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci

COPY . .

RUN cd frontend && npm run build

RUN cp tournamentapp/static/spa/.vite/manifest.json ./vite-manifest.json || true

EXPOSE 10000

CMD sh -c "\
    python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    gunicorn myproject.wsgi:application --bind 0.0.0.0:10000 --workers 3 --threads 2 --timeout 60"