from django.shortcuts import reverse, render, redirect
from django.contrib.auth import login

from . import forms


def log_in(request):
    if request.method == 'POST':
        login_form = forms.UserLoginForm(data=request.POST)
        if login_form.is_valid():
            user = login_form.get_user()
            login(request, user)
            return redirect("/")
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


