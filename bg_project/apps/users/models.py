from django.db import models
from django.conf import settings

from bg_project.apps.boardgames.models import BoardGame
from .services import get_user_profile_media_dir


class WishList(models.Model):
    """ Модель описывает Вишлист пользователя """
    user = models.OneToOneField(to=settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,)

    games = models.ManyToManyField(BoardGame, related_name="wish_lists")

    def __str__(self):
        return f"Wishlist пользователя {self.user}"


class Profile(models.Model):
    """ Модель описывает профиль пользователя.
        Создание Profile подвешено через сигнал на создание пользователя."""
    GENDERS = [
        ("M", "Мужской"),
        ("Ж", "Женский"),
    ]
    user = models.OneToOneField(to=settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE)

    photo = models.ImageField(upload_to=get_user_profile_media_dir, blank=True, null=True)
    email_confirmed = models.BooleanField(default=False)
    friendlist = models.ManyToManyField(to=settings.AUTH_USER_MODEL,
                                        related_name="friends")
    location = models.CharField(max_length=200)
    bio = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDERS, blank=True, null=True)
