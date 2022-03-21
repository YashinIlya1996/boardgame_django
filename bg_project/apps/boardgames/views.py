from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from .models import BoardGame


def test(request):
    """
    Первоначальное заполнение БД данными, которые спарсил с Тесеры, включая загрузку картинки игры
    Пусть останется для истории
    """
    import json
    import requests
    import re
    from django.conf import settings

    with open('all_games.json', 'rt') as f:
        l = json.load(f)

    games_count = len(l)
    for num, game in enumerate(l):
        photo_url = game.get('photo_url')
        alias = game['t_alias']
        title = game['title']
        description = game.get('description')
        if photo_url:
            try:
                extension = re.findall(r'\.\w+$', photo_url)[0]
            except IndexError as e:
                print(e, f"для {title}")
                extension = ""
            file_name = str(settings.BASE_DIR) + "/media/boardgames/main_bg_photo/" + alias + extension
            with open(file_name, 'wb') as f:
                f.write(requests.get(photo_url).content)
        BoardGame.objects.create(title=title,
                                 tesera_alias=alias,
                                 description=description or "Описание отсутствует",
                                 release_year=game.get('year'),
                                 bgg_rating=game.get('rating'),
                                 avg_game_time=game.get('avg_game_time') or 0,
                                 min_players_count=game.get('min_player') or 0,
                                 max_players_count=game.get('max_players') or game.get('min_player') or 0,
                                 tesera_id=game.get('tesera_id'),
                                 photo="boardgames/main_bg_photo/" + alias + extension if photo_url else None
                                 )
        print(f"Добавлена: {alias}, завершено на {num/games_count*100:.2f}% ({num} / {games_count})")
    return HttpResponse(f"В базу добавлено {games_count} игр")


def index(request):
    return render(request, 'boardgames/index.html')
