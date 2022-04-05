from bg_project.celery import app
from .services import parse_new_games


@app.task(name='celery_parse_new_games',
          bind=True,
          autoretry_for=(Exception, ),
          retry_kwargs={'max_retries': 5},
          retry_backoff=10)
def celery_parse_new_games(self):
    print("Начало парсинга")
    parse_new_games()
    print("Парсинг завершен")
