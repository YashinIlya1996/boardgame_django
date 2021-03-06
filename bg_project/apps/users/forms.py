import datetime as dt

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Profile, Meeting


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


class CreateMeetForm(forms.ModelForm):
    """ Форма для создания встречи.
        Поле creator берется из request.user во view, players вступают во встречу после ее создания"""

    class Meta:
        model = Meeting
        exclude = ('creator', 'players', 'in_request', 'notification_task_uuid')
        labels = {
            'description': 'Описание встречи',
            'date': 'Дата проведения',
            'time': 'Время проведения',
            'location': 'Место проведения',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean_date(self):
        if self.cleaned_data['date'] < dt.date.today():
            raise ValidationError('Дата не должна быть прошедшей')
        return self.cleaned_data['date']

    def clean_time(self):
        date = self.cleaned_data.get("date")
        if not date or self.cleaned_data['time'] < dt.datetime.now().time() and \
                date == dt.date.today():
            raise ValidationError('Время и дата не должны быть меньше текущего значения')
        return self.cleaned_data['time']
