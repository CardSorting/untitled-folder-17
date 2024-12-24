"""Task package initialization."""
from .companion_tasks import register_tasks as register_companion_tasks

# Import the celery app
from ..celery_app import celery

# Register tasks
task_registry = register_companion_tasks(celery)
process_companion_chat = task_registry['process_companion_chat']

__all__ = ['register_companion_tasks', 'process_companion_chat']
