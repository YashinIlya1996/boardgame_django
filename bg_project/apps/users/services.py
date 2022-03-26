""" Модуль для определения служебных функций """

from django.core.mail import EmailMessage


def code_to_confirm_email():
    # Генерирует случайный код для подтверждения почты при регистрации
    from random import randint
    return str(randint(100_000, 999_999))


def send_confirm_email(user_mail: str, confirm_code: int):
    # Отправляет письмо с кодом подтверждения регистрации пользователю
    mail = EmailMessage(
        to=[user_mail],
        subject="Подтверждение email",
        body=f"Для подтверждения email введите на сайте этот код: {confirm_code}"
    )
    for _ in range(10):     # Письмо отправляется 10 раз, если отправка не успешная
        send_ok = mail.send(fail_silently=True)
        if send_ok:
            break
    return send_ok


def get_user_profile_media_dir(instance, filename):
    """ Возвращает путь, в которую будет загружаться аватар пользователя """
    return f"users/{instance.user.id}/profile/{filename}"


