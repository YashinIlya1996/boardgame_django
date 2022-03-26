""" Модуль для регистрации и хранения сигналов, относящихся к приложению users
    Модуль импортируется в методе redy() конфигурационного класса приложения """

from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.core.exceptions import ObjectDoesNotExist

from .models import Profile, WishList


# Декоратор receiver(signal) аналогичен конструкции signal.connect(func_callback)
@receiver(post_save, sender=User)
def create_profile(sender, **kwargs):
    """ Сигнал создает экземпляр Profile, связанный с User, при создании нового User
        Сигнал на удаление не требуется, т.к. Profile on_delete=models.CASCADE """
    try:
        Profile.objects.get(user=kwargs['instance'])
    except ObjectDoesNotExist:
        Profile.objects.create(user=kwargs['instance'])


@receiver(post_save, sender=User)
def create_wishlist(sender, **kwargs):
    """ Создает Wishlist пользователя при регистрации """
    try:
        WishList.objects.get(user=kwargs["instance"])
    except ObjectDoesNotExist:
        WishList.objects.create(user=kwargs["instance"])