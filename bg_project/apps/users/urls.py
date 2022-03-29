from django.urls import path
from django.contrib.auth.views import (LogoutView,
                                       PasswordChangeView,
                                       PasswordChangeDoneView, )

from . import views

urlpatterns = [
    path("login/", views.log_in, name="log_in"),
    path("logout/", LogoutView.as_view(), name="log_out"),
    path("password_change/", PasswordChangeView.as_view(template_name='users/password_change.html'),
         name='password_change'),
    path("password_change_done/", PasswordChangeDoneView.as_view(template_name='users/password_change_done.html'),
         name='password_change_done'),
    path("signup/", views.sign_up, name="sign_up"),
    path("signup-confirm/", views.confirm_signup, name="confirm_sign_up"),
]
