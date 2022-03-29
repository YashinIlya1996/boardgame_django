from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Profile


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(), label="Имя пользователя")
    password = forms.CharField(widget=forms.PasswordInput(), label="Пароль")


class MyUserCreationForms(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(), label="Username")
    email = forms.EmailField(widget=forms.EmailInput(), required=False, label="Email")
    first_name = forms.CharField(required=False, label="Имя")
    last_name = forms.CharField(required=False, label="Фамилия")
    password1 = forms.CharField(widget=forms.PasswordInput(), label="Пароль")
    password2 = forms.CharField(widget=forms.PasswordInput(), label="Повторите пароль")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


class ConfirmEmailForm(forms.Form):
    code = forms.IntegerField(widget=forms.TextInput(attrs={"name": "code"}), label="Код подтвержденния")


class ProfileEditForm(forms.Form):
    fname = forms.CharField(required=False, widget=forms.TextInput(), label="Имя")
    lname = forms.CharField(required=False, widget=forms.TextInput(), label="Фамилия")
    location = forms.CharField(required=False, widget=forms.TextInput(), label="Город")
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={"style": "resize: none"}), label="О себе")
    gender = forms.ChoiceField(required=False, choices=Profile.GENDERS, label="Пол")
    photo = forms.ImageField(required=False, label="Новое фото")

    def clean_fname(self):
        fname = self.cleaned_data.get("fname")
        for digit in "0123456789":
            if digit in fname:
                raise ValidationError("Имя не должно содержать цифры.")
        return fname

    def clean_lname(self):
        lname = self.cleaned_data.get("lname")
        for digit in "0123456789":
            if digit in lname:
                raise ValidationError("Фамилия не должна содержать цифры.")
        return lname