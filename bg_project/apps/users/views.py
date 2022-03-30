from django.shortcuts import reverse, render, redirect, get_object_or_404
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.conf import settings

from .forms import UserLoginForm, MyUserCreationForms, ProfileEditForm, ConfirmEmailForm
from .models import WishList, Profile
from bg_project.apps.boardgames.models import BoardGame
from .services import apply_search_query_games, send_confirm_email
from .tasks import celery_send_confirm_email


def log_in(request):
    if request.method == 'POST':
        login_form = UserLoginForm(data=request.POST)
        if login_form.is_valid():
            user = login_form.get_user()
            login(request, user)
            return redirect(request.GET.get("next") or "index")
    else:
        login_form = UserLoginForm()
    return render(request, template_name="users/login.html", context={"form": login_form})


def sign_up(request):
    if request.method == 'POST':
        sign_up_form = MyUserCreationForms(data=request.POST)
        if sign_up_form.is_valid():
            if settings.EMAIL_CONFIRM_REQUIRED:
                # Если требуется подтверждение Email, отправляем пользователю код подтверждения на почту
                # и редирект на форму ввода проверочного кода
                user_data = sign_up_form.cleaned_data
                user = sign_up_form.save()
                user.is_active = False
                user.save()
                celery_send_confirm_email.delay(user.email, user.profile.email_confirm_code,
                                                reverse("confirm_sign_up", args=[user.username]))
                return redirect(reverse("confirm_sign_up", args=[user.username]))
            user = sign_up_form.save()
            login(request=request, user=user)
            return redirect("index")
    else:
        sign_up_form = MyUserCreationForms()
    return render(request, template_name="users/sign_up.html", context={"form": sign_up_form})


def confirm_signup(request, username):
    """ Подтверждение регистрации пользователя через код, направленный на email """
    user = get_object_or_404(User, username=username)
    if user.is_active:
        return redirect("profile_detail", user_id=user.id)
    if request.method == "POST":
        confirm_email_form = ConfirmEmailForm(request.POST)
        if confirm_email_form.is_valid():
            if user.profile.email_confirm_code == confirm_email_form.cleaned_data["code"]:
                user.is_active = True
                user.profile.email_confirmed = True
                user.save()
                user.profile.save()
                login(request, user)
                return redirect("profile_detail", user_id=user.id)
            else:
                confirm_email_form.errors["code"] = ['Неверный код подтверждения регистрации']
    else:
        confirm_email_form = ConfirmEmailForm()
    return render(request, "users/confirm_email.html", context={"form": confirm_email_form})


class UsersWishlistView(LoginRequiredMixin, ListView):
    """ Wishlist в виде списка игр, добавленных пользователем в ВЛ """
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

    def paginate_queryset(self, queryset, page_size):
        """ Переопределяет родительский метод для того, чтобы при удалении последней
            игры на странице из ВЛ не возвращалась 404, а переходил на последнюю страницу ВЛ """
        paginator = self.get_paginator(
            queryset,
            page_size,
            orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty(),
        )
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        try:
            page_number = int(page)
        except ValueError:
            page_number = paginator.num_pages
        page = paginator.get_page(page_number)
        return (paginator, page, page.object_list, page.has_other_pages())


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


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """ Информация о профиле пользователя """
    model = Profile
    context_object_name = "profile"
    template_name = "users/profile.html"

    def get_object(self, queryset=None):
        """ В качестве аргумента в роуте указан user_id, профиль которого требуется отобразить.
            Возвращает объект профиля по user_id или поднимает 404 """
        obj = get_object_or_404(Profile, user_id=self.kwargs["user_id"])
        return obj

    def get_context_data(self, **kwargs):
        """ Добавляет в контекст шаблона френдлист пользователя, чтобы не генерировать запрос внутри шаблона """
        context = super().get_context_data(**kwargs)
        context["friendlist"] = self.get_object().friendlist.all()
        context["owner"] = self.kwargs["user_id"] == self.request.user.id
        return context


@login_required
def profile_editing(request, user_id):
    """ Редактирование профиля запрещено пользователям, чей id не совпадает с user_id в роуте
        При отсутствии новой информации старая не изменяется. """
    user = User.objects.get(pk=user_id)
    if request.user.id != user.id:
        raise PermissionDenied("У Вас нет прав редактировать профиль другого пользователя.")
    p = Profile.objects.get(user=user)
    old_data = {"fname": user.first_name,
                "lname": user.last_name,
                "location": p.location,
                "bio": p.bio,
                "gender": p.gender,
                "photo": p.photo}
    if request.method == "POST":
        form = ProfileEditForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            user.last_name = cd.get("lname") or old_data["lname"]
            user.first_name = cd.get("fname") or old_data["fname"]
            p.location = cd.get("location") or old_data["location"]
            p.bio = cd.get("bio") or old_data["bio"]
            p.gender = cd.get("gender") or old_data["gender"]
            p.photo = cd.get("photo") or old_data["photo"]
            p.save()
            user.save()
            return redirect("profile_detail", user_id)
    else:
        form = ProfileEditForm(data=old_data)
    return render(request, "users/profile_editing.html", context={"form": form})
