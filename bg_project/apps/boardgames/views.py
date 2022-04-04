# Django импорт
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import ListView, DetailView
from django.db.models import F, Q
from django.core.exceptions import ObjectDoesNotExist

# DRF импорт
from rest_framework import viewsets

# Собственный импорт
from .models import BoardGame
from .serializers import BoardGamesListSerializer
from .services import get_queryset_bg_by_default_ordering
from bg_project.apps.users.services import apply_search_query_games
from .tasks import celery_parse_new_games


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
        print(f"Добавлена: {alias}, завершено на {num / games_count * 100:.2f}% ({num} / {games_count})")
    return HttpResponse(f"В базу добавлено {games_count} игр")


def clear_search_data(request):
    """
    Удаляет из сессии поисковый запрос и редиректит на предыдущую страницу
    """
    request.session["search"] = None
    return redirect(request.GET.get("next") or "all_games")


def index(request):
    return render(request, 'boardgames/index.html')


class AllGames(ListView):
    template_name = 'boardgames/all_games.html'
    context_object_name = 'all_games'
    paginate_by = 10

    def get_queryset(self):
        queryset = get_queryset_bg_by_default_ordering()
        queryset = apply_search_query_games(queryset, self.request)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        """
        Если пользователь авторизован, в контекст шаблона добавляем его вишлист,
        чтобы правильно обрабатывать состояние кнопки "Добавить в/Удалить из вишлист(а)"
        Также добавляет строку поиска в сессии (при наличии)
        """
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            user = self.request.user
            try:
                users_wl = user.wishlist.games.all()
            except ObjectDoesNotExist:
                users_wl = []
            context["users_wl"] = users_wl
        search = self.request.session.get("search")
        if search:
            context["search_str"] = search
        context["count"] = BoardGame.objects.count()
        return context


class DetailGame(DetailView):
    template_name = "boardgames/detail_game.html"
    context_object_name = "game"
    slug_url_kwarg = "alias"
    slug_field = "tesera_alias"

    def get_queryset(self):
        return BoardGame.objects.filter(tesera_alias=self.kwargs.get("alias"))


class BoardGameViewSet(viewsets.ModelViewSet):
    serializer_class = BoardGamesListSerializer
    queryset = get_queryset_bg_by_default_ordering()


def test_celery_downloader(request):
    celery_parse_new_games.delay()
    return HttpResponse("Парсинг запущен")