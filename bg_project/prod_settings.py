from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent

with open(BASE_DIR / 'secrets.json', 'rt') as s:
    secrets = json.load(s)

SECRET_KEY = secrets['SECRET_KEY']

STATIC_ROOT = BASE_DIR / 'static'

DEBUG = False

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': secrets['DB_NAME'],
        'HOST': secrets['DB_HOST'],
        'PORT': secrets['DB_PORT'],
        'USER': secrets['DB_USER_PROD'],
        'PASSWORD': secrets['DB_PASSWORD'],
    }
}