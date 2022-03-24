from django.template import Library

register = Library()


@register.filter(name="url_with_anchor")
def url_with_anchor(value, request):
    anchor = f"#{value.tesera_alias}"
    page = request.GET.get('page', 1)
    url = request.path + f"?page={page}" + anchor
    return url
