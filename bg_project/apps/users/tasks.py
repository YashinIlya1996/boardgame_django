from .services import send_confirm_email, send_meet_soon_notifications
from bg_project.celery import app

@app.task
def celery_send_confirm_email(user_mail: str, confirm_code: int, path: str):
    send_confirm_email(user_mail, confirm_code, path)


@app.task
def celery_send_meet_soon_notifications(meet_id: int):
    send_meet_soon_notifications(meet_id)