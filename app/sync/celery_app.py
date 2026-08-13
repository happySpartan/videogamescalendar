"""Celery app for the video game calendar background jobs.

Owns the broker/backend URL (single ``REDIS_URL``) and the beat schedule. The
worker tasks in ``app.sync.worker`` are registered on this app, and the admin
API enqueues tasks through it — so dispatcher and consumer always share the
same broker, avoiding the historical ``/0`` vs ``/1`` Redis DB mismatch.

Beats:
    hourly  delta game sync
    daily   full game sync (2am)
    weekly  data cleanup   (Sunday 3am)
"""
from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = Celery(
    "data_sync",
    broker=redis_url,
    backend=redis_url,
    include=["app.sync.worker"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # All tasks run on the single default queue; the worker consumes it directly,
    # so tasks enqueued from the admin API are always picked up.
    beat_schedule={
        "daily-full-sync": {
            "task": "data_sync.sync_games",
            "schedule": crontab(hour=2, minute=0),
            "kwargs": {"full_sync": True},
        },
        "hourly-delta-sync": {
            "task": "data_sync.sync_games",
            "schedule": crontab(minute=0),
            "kwargs": {"full_sync": False},
        },
        "weekly-cleanup": {
            "task": "data_sync.cleanup_old_data",
            "schedule": crontab(day_of_week=0, hour=3, minute=0),
        },
    },
)
