from django.shortcuts import reverse, render, redirect
from django.views.generic.list import ListView
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.conf import settings

from . import forms
from .models import WishList
from bg_project.apps.boardgames.models import BoardGame
from .services import apply_search_query_games


def log_in(request):
    if request.method == 'POST':
        login_form = forms.UserLoginForm(data=request.POST)
        if login_form.is_valid():
            user = login_form.get_user()
            login(request, user)
            return redirect(request.GET.get("next") or "index")
    else:
        login_form = forms.UserLoginForm()
    return render(request, template_name="users/login.html", context={"form": login_form})


def sign_up(request):
    if request.method == 'POST':
        sign_up_form = forms.MyUserCreationForms(data=request.POST)
        if sign_up_form.is_valid():
            user = sign_up_form.save()
            login(request=request, user=user)
            return redirect("index")
    else:
        sign_up_form = forms.MyUserCreationForms()
    return render(request, template_name="users/sign_up.html", context={"form": sign_up_form})


def confirm_signup(request):
    pass


class UsersWishlistView(LoginRequiredMixin, ListView):
    login_url = "log_in"
    redirect_field_name = "next"
    template_name = 'users/wishlist.html'
    paginate_by = 10
    context_object_name = "wishlist"

    def get_queryset(self):
        """
        Передает в queryset игры из вишлиста пользователя, применяя, при наличии, фильтр поиска
        """
        games = WishList.objects.get(user=self.request.user).games.all()
        games = apply_search_query_games(games, self.request)
        return games

    def get_context_data(self, *, object_list=None, **kwargs):
        """
        Добавляет в контекст шаблона вишлист пользователя,
        чтобы правильно обрабатывать состояние кнопки "Добавить в/Удалить из ВЛ"
        Также добавляет в контекст текстовый запрос из сессии, при наличии
        """
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            user = self.request.user
            try:
                users_wl = user.wishlist.games.all()
            except ObjectDoesNotExist:
                users_wl = []
            context["users_wl"] = users_wl
        if search := self.request.session.get("search"):
            context["search_str"] = search
        return context


def add_to_remove_from_wishlist(request, alias):
    """
    Обработчик кнопки добавления (удаления) игры в (из) вишлист(а).
    Если игра уже в ВЛ (запрос на удаление игры из ВЛ) - удаляет ее из ВЛ.
    Если каким-то чудом запрос на добавление послал аноним - редирект на логин.
    """
    if not request.user.is_authenticated:
        return redirect("log_in")
    else:
        user = request.user
        game = BoardGame.objects.get(tesera_alias=alias)
        wl = user.wishlist
        if game not in wl.games.all():
            user.wishlist.games.add(game)
        else:
            user.wishlist.games.remove(game)
    return redirect(request.GET.get("next"), "all_games")
    # TODO реализовать при удалении со страницы Wishlist правильный редирект на Wishlist (поковыряться в фильтре)
