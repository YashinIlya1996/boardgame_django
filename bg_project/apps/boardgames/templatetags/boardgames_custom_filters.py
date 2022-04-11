from django.template import Library

register = Library()


@register.filter(name="url_with_anchor")
def url_with_anchor(value, full_path):
    anchor = f"#{value.tesera_alias}"
    url = full_path + anchor
    return url


@register.filter(name="unread_notifications_count")
def unread_notifications_count(user):
    """ Возвращает количество непрочитанных уведомлений пользователя """
    return user.notifications.filter(is_read=False).count()
