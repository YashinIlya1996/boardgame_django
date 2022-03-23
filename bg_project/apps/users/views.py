from django.shortcuts import reverse, render, redirect
from django.views.generic.list import ListView
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist

from . import forms
from .models import WishList


def log_in(request):
    if request.method == 'POST':
        login_form = forms.UserLoginForm(data=request.POST)
        if login_form.is_valid():
            user = login_form.get_user()
            login(request, user)
            return redirect(request.GET.get("next") or "index")
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


class UsersWishlistView(LoginRequiredMixin, ListView):
    login_url = "log_in"
    redirect_field_name = "next"
    template_name = 'users/wishlist.html'
    paginate_by = 10
    context_object_name = "wishlist"

    def get_queryset(self):
        print(self.request.user == WishList.objects.all()[0].user)
        try:
            games = WishList.objects.get(user=self.request.user).games.all()
        except ObjectDoesNotExist:
            games = []
        return games
