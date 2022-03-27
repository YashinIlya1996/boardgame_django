from django.template import Library

register = Library()


@register.filter(name="url_with_anchor")
def url_with_anchor(value, full_path):
    anchor = f"#{value.tesera_alias}"
    url = full_path + anchor
    return url
