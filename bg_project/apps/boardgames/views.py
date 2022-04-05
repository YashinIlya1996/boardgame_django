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

