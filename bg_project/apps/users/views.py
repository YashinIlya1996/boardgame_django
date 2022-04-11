from django.shortcuts import reverse, render, redirect, get_object_or_404
from django.http.response import Http404
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.conf import settings

from .forms import UserLoginForm, MyUserCreationForms, ProfileEditForm, ConfirmEmailForm, CreateMeetForm
from .models import WishList, Profile, FriendshipQuery, Meeting, Notification
from bg_project.apps.boardgames.models import BoardGame
from .services import (apply_search_query_games,
                       apply_search_query_profiles,
                       is_friends,
                       make_friends,
                       unmake_friends,
                       is_meet_creator,
                       send_notification,
                       )
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
    return render(request, template_name="users/login.html", context={"form": login_form, "active": "login"})


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
    return render(request, template_name="users/sign_up.html", context={"form": sign_up_form, "active": "signup"})


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
    return render(request, "users/confirm_email.html", context={"form": confirm_email_form, "active": "signup"})


class UsersWishlistView(LoginRequiredMixin, ListView):
    """ Wishlist в виде списка игр, добавленных пользователем в ВЛ """
    login_url = "log_in"
    redirect_field_name = "next"
    template_name = 'users/wishlist.html'
    paginate_by = 10
    context_object_name = "wishlist"

    def get(self, *args, **kwargs):
        user_id = self.kwargs.get("user_id")
        if user_id:
            friend = get_object_or_404(User, pk=user_id)
            if self.request.user not in friend.profile.friendlist.all():
                raise PermissionDenied
        return super(UsersWishlistView, self).get(*args, **kwargs)

    def get_queryset(self):
        """ Передает в queryset игры из вишлиста пользователя, применяя, при наличии, фильтр поиска """
        user_id = self.kwargs.get("user_id", self.request.user.id)
        try:
            games = WishList.objects.get(user_id=user_id).games.all()
        except ObjectDoesNotExist:
            raise Http404
        games = apply_search_query_games(games, self.request)
        return games

    def get_context_data(self, *, object_list=None, **kwargs):
        """
        Добавляет в контекст шаблона вишлист пользователя,
        чтобы правильно обрабатывать состояние кнопки "Добавить в/Удалить из ВЛ"
        Также добавляет в контекст текстовый запрос из сессии, при наличии
        """
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get("user_id", self.request.user.id)
        context["user_owner_name"] = get_object_or_404(User, pk=user_id).get_full_name()
        if self.request.user.is_authenticated:
            user = self.request.user
            try:
                users_wl = user.wishlist.games.all()
            except ObjectDoesNotExist:
                users_wl = []
            context["users_wl"] = users_wl
        if search := self.request.session.get("search"):
            context["search_str"] = search
        context["active"] = "wishlist"
        context["user_owner"] = self.kwargs.get("user_id", self.request.user.id)
        context["owner"] = self.request.user.id == self.kwargs.get("user_id", self.request.user.id)
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


class MeetsListView(ListView):
    """ Отображение списка созданных встреч. """
    template_name = 'users/meets.html'
    paginate_by = 10
    context_object_name = 'meets'

    def get_queryset(self):
        # return [x for x in Meeting.objects.all() if not x.finished]
        category = self.kwargs["category"]
        if not self.request.user.is_authenticated or category == "future":
            return [x for x in Meeting.objects.all() if not x.finished]
        elif category == "im-creator":
            return self.request.user.created_meets.all()
        elif category == "with-my-participation":
            return self.request.user.meets.all()
        elif category == "past":
            return [x for x in Meeting.objects.all() if x.finished]

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(MeetsListView, self).get_context_data(object_list=object_list, **kwargs)
        context["active"] = "meets"
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
        qlist = self.request.GET.get("list")
        if qlist not in ("to-me", "from-me"):
            context["friendlist"] = self.get_object().friendlist.all()
            context["fl_template_name"] = "users/friendlists/all_friends_in_my_fl.html"
        elif qlist == "to-me":
            context["friendlist"] = [u.sender for u in self.get_object().user.friendship_queries_to_me.select_related()]
            context["fl_template_name"] = "users/friendlists/users_in_friendship_queries_to_me.html"
        elif qlist == "from-me":
            context["friendlist"] = [u.receiver for u in
                                     self.get_object().user.friendship_queries_from_me.select_related()]
            context["fl_template_name"] = "users/friendlists/users_in_friendship_queries_from_me.html"
        owner = self.kwargs["user_id"] == self.request.user.id
        context["owner"] = owner
        profiles = [fq.sender.profile for fq in self.request.user.friendship_queries_to_me.all()]
        context["profiles_from_friendship_notifications"] = profiles
        context["users_from_friendship_notifications"] = [p.user for p in profiles]
        context["active"] = "profile"
        if owner:
            context["read_notifications"] = self.request.user.notifications.filter(is_read=True)
            context["unread_notifications"] = self.request.user.notifications.filter(is_read=False)
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
    return render(request, "users/profile_editing.html", context={"form": form, 'active': 'profile'})


class ProfilesList(LoginRequiredMixin, ListView):
    """ Страница списка пользователей (для добавления во friendlist) """
    login_url = "log_in"
    redirect_field_name = "next"
    template_name = "users/profile_list.html"
    paginate_by = 6
    context_object_name = "profiles"

    def get_queryset(self):
        queryset = Profile.objects.exclude(user=self.request.user)
        return apply_search_query_profiles(queryset, self.request)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=None, **kwargs)
        context["users_friends_profiles"] = self.request.user.friends_profiles.all()
        context["active"] = "profile"
        if search := self.request.session.get("search_user"):
            context["search_str"] = search
        return context


@login_required
def send_friendship_query(request, user_id):
    """ Создает запрос на добавление в друзья от залогинившегося пользователя к пользователю с pk=user_id """
    sender = request.user
    receiver = get_object_or_404(User, pk=user_id)
    senders_friendlist = sender.friends_profiles.all()
    if receiver.profile in senders_friendlist:
        return redirect("profile_detail", user_id=sender.id)
    FriendshipQuery.objects.get_or_create(sender=sender, receiver=receiver)
    return redirect(request.META.get("HTTP_REFERER") or "all_games")


@login_required
def confirm_friendship_query(request, user_id):
    """ Принимает запрос со стороны залогинившегося пользователя на добавление в друзья от пользователя pk=user_id """
    receiver = request.user
    sender = get_object_or_404(User, pk=user_id)
    friendship_query = get_object_or_404(FriendshipQuery, receiver_id=receiver.id, sender_id=sender.id)
    if not is_friends(receiver, sender):
        make_friends(receiver, sender)
    friendship_query.delete()
    return redirect(request.META.get('HTTP_REFERER', reverse("profile_detail", args=[receiver.id])))


@login_required
def reject_friendship_query(request, user_id):
    """ Отклоняет запрос со стороны залогинившегося пользователя на добавление в друзья от пользователя pk=user_id """
    receiver = request.user
    sender = get_object_or_404(User, pk=user_id)
    friendship_query = get_object_or_404(FriendshipQuery, receiver_id=receiver.id, sender_id=sender.id)
    # Если они уже друзья (например, при взаимных одновременных запросах), удаляем из ФЛ
    if is_friends(receiver, sender):
        unmake_friends(receiver, sender)
    friendship_query.delete()
    return redirect(request.META.get('HTTP_REFERER', reverse("profile_detail", args=[receiver.id])))


@login_required
def cancel_friendship_query(request, user_id):
    """ Отменяет запрос на добавление в друзья, созданный залогинившимся пользователем в адрес пользователя user_id"""
    FriendshipQuery.objects.filter(sender_id=request.user.pk, receiver_id=user_id).delete()
    return redirect(request.META.get('HTTP_REFERER', reverse("profile_detail", args=[request.user.id])))


@login_required
def delete_from_friendlist(request, user_id):
    """ Удаляет пользователя с pk=user_id из ФЛ залогинившегося пользователя """
    deleted_user = get_object_or_404(User, pk=user_id)
    unmake_friends(request.user, deleted_user)
    return redirect(request.META.get('HTTP_REFERER', reverse("profile_detail", args=[request.user.id])))


@login_required
def create_meet(request):
    """ Обраотка страницы создания встречи """
    if request.method == 'POST':
        form = CreateMeetForm(data=request.POST)
        creator = request.user
        if form.is_valid():
            new_meet = form.save(commit=False)
            new_meet.creator = creator
            new_meet.save()
            friendlist = creator.profile.friendlist.values_list('pk', flat=True)
            message = f"Ваш друг {creator.get_full_name()} ({creator.username}) создал новую" \
                      f' <a href="{new_meet.get_absolute_url()}">встречу</a>!'
            send_notification(friendlist, message)
            return redirect("meets", "future")
    else:
        form = CreateMeetForm()
    return render(request, 'users/meet_creation.html', context={'form': form})


@login_required
def send_meet_request(request, meet_id):
    """ Отправляет запрос на участие во встрече"""
    meet = get_object_or_404(Meeting, pk=meet_id)
    sender = request.user
    if sender not in meet.players.all() and sender != meet.creator:
        sender.meets_in_request.add(meet)
    return redirect(request.META.get('HTTP_REFERER', reverse("meets", args=["future"])))


@login_required
def leave_meet_and_cancel_meet_request(request, meet_id):
    """ Отменяет заявку пользователя на участие во встрече """
    # meet = get_object_or_404(Meeting, pk=meet_id)
    try:
        meet = Meeting.objects.prefetch_related('players', 'in_request').get(pk=meet_id)
    except ObjectDoesNotExist:
        raise Http404
    user = request.user
    if user in meet.players.all():
        user.meets.remove(meet)
    if user in meet.in_request.all():
        user.meets_in_request.remove(meet)
    return redirect(request.META.get('HTTP_REFERER', reverse("meets", args=["future"])))


@login_required
def reject_meet_request(request, meet_id, user_id):
    """ Отклоняет запрос на участие пользователя user_id во встрече meet_id """
    if not is_meet_creator(request, meet_id):
        raise PermissionDenied("У вас недостаточно прав, чтобы управлять встречей")
    meet = get_object_or_404(Meeting, pk=meet_id)
    not_player = get_object_or_404(User, pk=user_id)
    meet.in_request.remove(not_player)
    return redirect(request.META.get('HTTP_REFERER', reverse("meets", args=["future"])))


@login_required
def confirm_meet_request(request, meet_id, user_id):
    """ Принимает запрос на участие во встрече """
    if not is_meet_creator(request, meet_id):
        raise PermissionDenied("У вас недостаточно прав, чтобы управлять встречей")
    meet = get_object_or_404(Meeting, pk=meet_id)
    player = get_object_or_404(User, pk=user_id)
    meet.players.add(player)
    meet.in_request.remove(player)
    return redirect(request.META.get('HTTP_REFERER', reverse("meets", args=["future"])))


@login_required
def delete_from_players(request, meet_id, user_id):
    """ Удаляет пользователя user_id из встречи meet_id """
    if not is_meet_creator(request, meet_id):
        raise PermissionDenied("У вас недостаточно прав, чтобы управлять встречей")
    meet = get_object_or_404(Meeting, pk=meet_id)
    player = get_object_or_404(User, pk=user_id)
    meet.players.remove(player)
    return redirect(request.META.get('HTTP_REFERER', reverse("meets", args=["future"])))


@login_required
def manage_meeting(request, meet_id):
    """ Управление встречей, созданной пользователем"""
    if not is_meet_creator(request, meet_id):
        raise PermissionDenied("У вас недостаточно прав, чтобы управлять встречей")
    meet = get_object_or_404(Meeting, pk=meet_id)
    return render(request, "users/meet_manage.html", context={'meet': meet,
                                                              'active': 'meets'})


class MeetDetail(DetailView):
    """ Детальная страница встречи"""
    model = Meeting
    context_object_name = "meet"
    template_name = "users/meet_detail.html"

    def get(self, request, *args, **kwargs):
        """ Создатель встречи перенаправляется на страницу управления встречей """
        user = request.user
        if user.is_authenticated:
            meet_pk = self.kwargs.get("meet_pk")
            meet_creator = Meeting.objects.get(pk=meet_pk).creator
            if user == meet_creator:
                return redirect("manage_meeting", meet_pk)
        return super(MeetDetail, self).get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        try:
            meet = Meeting.objects.prefetch_related('players', 'in_request').get(pk=self.kwargs["meet_pk"])
            return meet
        except ObjectDoesNotExist:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active"] = "meets"
        return context


@login_required
def read_notification(request, not_id=None):
    """ Устанавливает статус is_read уведомлению pk=not_id или всем уведомлениям пользователя,
        если not_id is None"""
    if not not_id:
        request.user.notifications.all().update(is_read=True)
    else:
        notification = get_object_or_404(Notification, pk=not_id)
        if request.user.pk != notification.user.pk:
            raise PermissionDenied("Чужое уведомление")
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    return redirect(request.META.get('HTTP_REFERER', reverse("profile_detail", args=[request.user.pk])))
