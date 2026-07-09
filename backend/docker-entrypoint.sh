#!/bin/sh
# Run pending migrations, then hand off to uvicorn. Baked into the image (rather
# than passed as a platform-specific "start command" override) so it behaves the
# same under docker-compose, Render, or any other Docker host.
set -e
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
