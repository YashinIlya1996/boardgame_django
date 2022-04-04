from django.db.models import F, Max
from django.db.utils import IntegrityError
from django.conf import settings
from rest_framework.pagination import PageNumberPagination

import requests
import re
from html import unescape

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


def parse_new_games():
    """ Парсинг тесеры и добавление новых записей об играх в БД """
    # 1) Получаем максимальное значение tesera_id из записей в базе
    newest_tesera_id = BoardGame.objects.aggregate(newest=Max('tesera_id'))['newest']
    print(newest_tesera_id)
    # Будем парсить тесеру до того значения, пока оно не будет меньшим newest_tesera_id
    url = "https://api.tesera.ru/games/"
    current_page = 0  # текущая страница в запросе к API тесеры
    limit = 100  # максимальное возможное количесво результатов в одном запросе
    stop = False

    def is_not_fake(game: dict) -> bool:
        """ Через API тесеры также возвращаются "пустые" игры. Для них нужно проверить, существует ли
            реальная страница на тесере. При этом ответ на несуществующую игру будет 200, но html-страница
            представляет собой простой текст "объект {id} не существует" без какой-либо разметки"""
        if bool(game.get('description') or game.get('photoUrl')):
            try:
                game_page_url = requests.get(url + game['alias'], timeout=30).json()['game']['teseraUrl']
                html_page_game = requests.get(game_page_url, timeout=30).text
                return "!DOCTYPE" in html_page_game
            except requests.exceptions.Timeout:
                return False
        return False

    while True:
        """ Загружаем очередные 100 новых игр, если запись не пустая - добавляем в БД, если id меньше
            последнего в базе - останавливаем """
        page_obj = requests.get(url, params={'limit': limit, 'offset': current_page}, timeout=60).json()
        for game in page_obj:  # type: dict
            print(f'Page: {current_page} - {game.get("title")}')
            if game.get('id') <= newest_tesera_id:
                stop = True
                break
            if is_not_fake(game):
                # Заменяем в описании html-сущности и убираем тэги
                description = re.sub(r'<[^>]*>|\r|\n', '', unescape(game.get('description'))) if game.get(
                    'description') else None

                # Определяем среднее время партии, (может отсутствовать в response)
                min_time = game.get('playtimeMin')
                max_time = game.get('playtimeMax')
                if min_time and max_time:
                    avg_time = int(float(min_time) + float(max_time)) // 2
                else:
                    avg_time = min_time or max_time

                tesera_alias = game.get('alias')

                # работа с загрузкой изображения и сохранением в БД
                photo_url = game.get('photoUrl')
                default_photo_name = "boardgames/main_bg_photo/no-photo.jpeg"  # в БД при отсутствии фото
                if photo_url:
                    try:  # получаем расширение файла
                        extension = re.findall(r'\.\w+$', photo_url)[0]
                    except IndexError as e:
                        extension = ""

                    # Составляем новое имя файла и сохраняем фото в media
                    file_name = str(settings.BASE_DIR) + "/media/boardgames/main_bg_photo/" + tesera_alias + extension
                    with open(file_name, 'wb') as f:
                        f.write(requests.get(photo_url).content)
                    photo_name = "boardgames/main_bg_photo/" + tesera_alias + extension
                else:
                    photo_name = default_photo_name

                try:
                    last_saved = BoardGame.objects.create(
                        title=game["title"],
                        tesera_alias=tesera_alias,
                        description=description or "Описание отсутствует",
                        release_year=int(game.get('year')),
                        bgg_rating=float(game.get('bggRating')) or None,
                        avg_game_time=avg_time,
                        min_players_count=int(game.get('playersMin')) or 0,
                        max_players_count=int(game.get('playersMax')) or 0,
                        tesera_id=int(game.get('id')),
                        photo=photo_name)
                    print(f"Сохранено: {last_saved} ({last_saved.id})")
                except IntegrityError:
                    print(f"Игра с алиасом {tesera_alias} уже есть в БД")
        if stop: break
        current_page += 1
