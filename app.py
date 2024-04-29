from flask import Flask
from celery import Celery
from celery.schedules import crontab

# Celery configuration (adjust broker URL if needed)
app = Celery('tasks', broker='amqp://localhost')

# Flask application initialization
flask_app = Flask(__name__)

# Import tasks from tasks.py
from tasks import update_index_file, get_data_from_sheets, send_poll, send_message

@flask_app.route('/')
def index():
  last_question_index = update_index_file()
  print(f"Last question index: {last_question_index}")

  data = get_data_from_sheets(last_question_index)
  if data:
    question = data["question"]
    answers = data["answers"]
    correct_answer = data["correct_answer"]

    send_poll.delay(question, answers)
    # Trigger send_message with a 30-minute delay (1800 seconds)
    send_message.delay.apply_async(args=(correct_answer,), countdown=1800)
    print("...one cycle...")

  return "Celery background tasks are running!"


# Celery Beat configuration for scheduled tasks
CELERY_BEAT_SCHEDULE = {
    'update_index': {
        'task': 'tasks.update_index_file',  # Replace with actual function name
        'schedule': crontab(minute='*/60'),  # Runs every 60 minutes
    }
}


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  flask_app.run(host='0.0.0.0', port=port)
