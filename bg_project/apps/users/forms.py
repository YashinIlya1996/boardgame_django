from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(), label="Имя пользователя")
    password = forms.CharField(widget=forms.PasswordInput(), label="Пароль")


class MyUserCreationForms(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(), label="Имя пользователя")
    email = forms.EmailField(widget=forms.EmailInput(), required=False, label="Email")
    first_name = forms.CharField(required=False, label="Имя")
    last_name = forms.CharField(required=False, label="Фамилия")
    password1 = forms.CharField(widget=forms.PasswordInput(), label="Пароль")
    password2 = forms.CharField(widget=forms.PasswordInput(), label="Повторите пароль")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


class ConfirmEmailForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={"name": "code"}), label="Код подтвержденния")

