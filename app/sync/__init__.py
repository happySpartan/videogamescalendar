"""Celery worker + beat for the video game calendar.

Consolidated into the ``app`` package. The worker and the admin API share this
single ``celery_app`` (and therefore a single ``REDIS_URL`` broker), so tasks
enqueued from the admin UI are guaranteed to be seen by the worker.
"""
