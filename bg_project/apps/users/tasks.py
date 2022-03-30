from .services import send_confirm_email
from bg_project.celery import app

@app.task
def celery_send_confirm_email(user_mail: str, confirm_code: int, path: str):
    send_confirm_email(user_mail, confirm_code, path)