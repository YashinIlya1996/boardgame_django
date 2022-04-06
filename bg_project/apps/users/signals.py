""" Модуль для регистрации и хранения сигналов, относящихся к приложению users
    Модуль импортируется в методе redy() конфигурационного класса приложения """

import datetime as dt
import uuid

from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.utils import timezone
from django.conf import settings
from celery.result import AsyncResult

from .models import Profile, WishList, Meeting
from . import tasks


# Декоратор receiver(signal) аналогичен конструкции signal.connect(func_callback)
@receiver(post_save, sender=User)
def create_profile(sender, **kwargs):
    """ Сигнал создает экземпляр Profile, связанный с User, при создании нового User
        Сигнал на удаление не требуется, т.к. Profile on_delete=models.CASCADE """
    if not hasattr(kwargs['instance'], 'profile'):
        Profile.objects.create(user=kwargs['instance'])


@receiver(post_save, sender=User)
def create_wishlist(sender, **kwargs):
    """ Создает Wishlist пользователя при регистрации """
    if not hasattr(kwargs['instance'], 'wishlist'):
        WishList.objects.create(user=kwargs["instance"])


@receiver(post_save, sender=Meeting)
def create_email_notification_celery_task(sender, **kwargs):
    """ При сохранении объекта встречи создает отложенную задачу celery
        на оповещение пользователей по email за 3 часа до начала встречи(время оповещения до начала встречи
        регулируется в settings.TIME_BEFORE_MEET_NOTIFICATION)"""
    print(kwargs)
    if (not kwargs['update_fields']) or (
            kwargs['update_fields'] and 'notification_task_uuid' not in kwargs['update_fields']):
        meet = kwargs['instance']
        prev_id = meet.notification_task_uuid
        if prev_id:
            # Если ранее уже была создана таска на уведомление - нужно ее обновить
            AsyncResult(id=str(prev_id)).revoke(terminate=True)

        res = tasks.celery_send_meet_soon_notifications.apply_async(
            args=[meet.pk],
            eta=dt.datetime.combine(meet.date, meet.time, tzinfo=timezone.get_current_timezone()) - dt.timedelta(
                seconds=settings.TIME_BEFORE_MEET_NOTIFICATION)
        )
        meet.notification_task_uuid = uuid.UUID(res.id)
        meet.save(update_fields=('notification_task_uuid',))

