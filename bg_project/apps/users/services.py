""" Модуль для определения служебных функций """
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from . import models as user_models  # такой импорт для исключения циклического импорта


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
    user1.profile.friendlist.add(user2)
    # user2.friends_profiles.add(user1.profile)


def unmake_friends(user1, user2):
    """ Взаимно удаляет пользователей из френдлистов """
    user1.friends_profiles.remove(user2.profile)
    user1.profile.friendlist.remove(user2)
    # user2.friends_profiles.remove(user1.profile)


def is_meet_creator(request, meet_id):
    """ True, если залогинившийся пользователь - создатель встречи meet_id"""
    meet = get_object_or_404(user_models.Meeting, pk=meet_id)
    return request.user == meet.creator


def send_meet_soon_notifications(meet_id: int):
    """ Отправляет письма участникам встречи """
    meet = user_models.Meeting.objects.prefetch_related('players').get(pk=meet_id)
    emails = tuple({player.email for player in meet.players.all() if player.email})
    mail = EmailMessage(
        to=emails,
        subject="Скоро состоится встреча",
        body=f"Уважаемый пользователь! Это письмо направлено вам, потому что вы принимаете участие во встрече, " 
             f"которая состоится {meet.date.strftime('%d.%m.%Y')} в {meet.time.strftime('%H:%M')} " 
             f"по адресу {meet.location}. Приятной игры! " 
             f"P.S. Для уточнения деталей Вы можете связаться с организатором встречи по email: {meet.creator.email}"
    )
    for _ in range(10):  # Письмо отправляется 10 раз, если отправка не успешная
        send_ok = mail.send(fail_silently=True)
        if send_ok:
            break


def send_notification(users_id: list, message: str):
    """ Создает объект Notification всем пользователям pk in users_id с полем message=message"""
    users = User.objects.filter(pk__in=users_id)
    notifications = [user_models.Notification(user=user, message=message) for user in users]
    user_models.Notification.objects.bulk_create(notifications)
