from django.db.models import F
from rest_framework.pagination import PageNumberPagination
from .models import BoardGame


def get_queryset_bg_by_default_ordering():
    """ Общий для API и HTML порядок сортровки полученных значений.
        Учитывает сортировку значений с bgg_rating, release_year = null
        (без этой сортировки порядок значений с null не гарантируется БД)"""
    return BoardGame.objects.order_by(
        F('bgg_rating').desc(nulls_last=True), F('release_year').desc(nulls_last=True), F('tesera_alias'))


class PageNumberPageSizePagination(PageNumberPagination):
    """ Класс API пагинации с возможностью управлять количеством элементов на странице"""
    page_size_query_param = 'page_size'
