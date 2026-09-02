#!/bin/sh
set -e
case "${MELA_SERVICE:-api}" in
  bot)
    exec python -m app.bot.bot
    ;;
  worker)
    exec celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
    ;;
  beat)
    exec celery -A app.workers.celery_app beat --loglevel=info
    ;;
  *)
    exec sh scripts/start-api.sh
    ;;
esac
