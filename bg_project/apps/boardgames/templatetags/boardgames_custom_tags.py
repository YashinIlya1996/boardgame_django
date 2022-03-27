from django import template

register = template.Library()


@register.inclusion_tag(filename='boardgames/game_in_list.html', name="list_item_game", takes_context=True)
def print_game_in_list(context):
    """ Возвращает представление игры в общем листе при отображении в общем перечне игр
        и в вишлисте пользователя.
        full_path требуется для редиректа на ту же игру на странице через якорь """
    full_path = context["request"].get_full_path()
    odd_even = "even" if context["forloop"]["counter"] % 2 else "odd"
    return {"game": context["game"],
            "user": context["user"],
            "full_path": full_path,
            "users_wl": context["users_wl"],
            "odd_even": odd_even}
