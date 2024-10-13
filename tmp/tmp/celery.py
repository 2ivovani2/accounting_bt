# your_project/celery.py
import os
from celery import Celery

app = Celery('tmp')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()