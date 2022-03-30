""" Модуль для определения служебных функций """
from django.core.mail import EmailMessage
from time import sleep


def code_to_confirm_email():
    """ Генерирует случайный код для подтверждения почты при регистрации"""
    from random import randint
    return str(randint(100_000, 999_999))


def send_confirm_email(user_mail: str, confirm_code: int, path: str):
    """Отправляет письмо с кодом подтверждения регистрации пользователю"""
    mail = EmailMessage(
        to=[user_mail],
        subject="Подтверждение email",
        body=f"Для подтверждения email введите на странице {path} этот код: {confirm_code}"
    )
    for _ in range(10):  # Письмо отправляется 10 раз, если отправка не успешная
        send_ok = mail.send(fail_silently=True)
        if send_ok:
            break


def get_user_profile_media_dir(instance, filename):
    """ Возвращает путь, в которую будет загружаться аватар пользователя """
    return f"users/{instance.user.id}/profile/{filename}"


def apply_search_query_games(queryset, request):
    """ Применяет поисковый запрос к списку игр, переданный в запросе или хранящийся в сессии"""
    search = request.GET.get("search") or request.session.get("search") or ""
    request.session["search"] = search
    return queryset.filter(title__icontains=search)


def is_friends(user1, user2):
    """ Определяет, являются ли user1 и user2 друзьями """
    return user1.profile in user2.friends_profiles.all() and user2.profile in user1.friends_profiles.all()


def make_friends(user1, user2):
    """ Взаимно добавляет пользователей во френдлисты """
    user1.friends_profiles.add(user2.profile)
    user2.friends_profiles.add(user1.profile)


def unmake_friends(user1, user2):
    """ Взаимно удаляет пользователей из френдлистов """
    user1.friends_profiles.remove(user2.profile)
    user2.friends_profiles.remove(user1.profile)