from celery import Celery
from celery.schedules import crontab

app = Celery('tasks', broker='amqp://localhost')

# ... other Celery configuration options (if needed)

CELERY_BEAT_SCHEDULE = {
    'process_questions': {
        'task': 'bot.index',  # Replace 'your_app' with your actual module name
        'schedule': crontab(minute='*/60'),  # Runs every 30 minutes
    }
}
