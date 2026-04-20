"""Celery task wrapper to run a single ``TaskExecution`` through its parent job's agent."""

from __future__ import annotations

from celery import shared_task
from celery.utils.log import get_task_logger

from core.services.task_execution_runner import run_task_execution as _runner

logger = get_task_logger(__name__)


@shared_task(bind=True)
def run_task_execution(self, task_execution_id: str):
    """Run one ``TaskExecution`` end-to-end (agent loop + outputs persistence)."""
    return _runner(task_execution_id, celery_task_id=self.request.id)
