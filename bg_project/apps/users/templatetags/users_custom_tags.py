from django import template

register = template.Library()


@register.inclusion_tag(filename="users/user_in_list.html", name="list_item_user")
def print_user_in_list(user_to_print, button=None):
    """ Возвращает представление пользователя в списке пользователей.
        Отображение и ссылка кнопки на взаимодействие с пользователем зависят от значения переменной button
        в контексте. """
    return {
        "user_to_print": user_to_print,
        "button": button
    }
