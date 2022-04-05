import os

from celery import Celery
from celery.beat import crontab

#  указываем путь до конфигурационного файла проекта
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bg_project.settings')

app = Celery('bg_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
# Требуется для автоматического поиска всех задач, обернутых в @app.task
# Т.к. не указан атрибут related_name. по умолчанию будет искать в файлах tasks.py
app.autodiscover_tasks()

""" Для того чтобы app подгружался при запуске проекта, app нужно импортировать в __init__.py проекта
    и указать в __all__ там же """

""" Настройка расписания периодической задачи на обновление списка игр BoardGames"""
app.conf.beat_schedule = {
    'parse_tesera_every_day': {
        'task': 'celery_parse_new_games',
        'schedule': crontab(minute='0', hour='4'),
    }
}
