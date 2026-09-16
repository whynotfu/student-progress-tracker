#!/bin/sh
set -e

# db.create_all() в create_app() создаёт таблицы, если их ещё нет;
# seed.py идемпотентен (проверяет наличие записей перед вставкой),
# поэтому его безопасно гонять при каждом старте контейнера.
python seed.py

mkdir -p /app/logs
exec gunicorn -w 2 -b 0.0.0.0:8000 \
    --access-logfile /app/logs/access.log \
    --error-logfile /app/logs/error.log \
    wsgi:app
