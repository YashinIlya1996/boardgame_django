from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import ListView, DetailView
from django.db.models import F, Q
from django.core.exceptions import ObjectDoesNotExist

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
        print(f"Добавлена: {alias}, завершено на {num / games_count * 100:.2f}% ({num} / {games_count})")
    return HttpResponse(f"В базу добавлено {games_count} игр")


def index(request):
    return render(request, 'boardgames/index.html')


class AllGames(ListView):
    template_name = 'boardgames/all_games.html'
    queryset = BoardGame.objects.order_by(
        F('bgg_rating').desc(nulls_last=True), F('release_year').desc(nulls_last=True), F('tesera_alias'))
    context_object_name = 'all_games'
    paginate_by = 10

    def get_context_data(self, *, object_list=None, **kwargs):
        """
        Если пользователь авторизован, в контекст шаблона добавляем его вишлист,
        чтобы правильно обрабатывать состояние кнопки "Добавить в/Удалить из вишлист(а)"
        """
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            user = self.request.user
            try:
                users_wl = user.wishlist.games.all()
            except ObjectDoesNotExist:
                users_wl = []
            context["users_wl"] = users_wl
        return context


class DetailGame(DetailView):
    template_name = "boardgames/detail_game.html"
    context_object_name = "game"
    slug_url_kwarg = "alias"
    slug_field = "tesera_alias"

    def get_queryset(self):
        return BoardGame.objects.filter(tesera_alias=self.kwargs.get("alias"))

