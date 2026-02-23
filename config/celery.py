import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module for 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('mfp_backend') # Matches your folder name

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "dispatch-meta-refresh": {
        "task": "apps.social_accounts.tasks.dispatch_expiring_meta_refresh_tasks",
        "schedule": crontab(minute=0, hour="*/12"),
    },
}