from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views

urlpatterns = [
    path("login/", views.log_in, name="log_in"),
    path("logout/", LogoutView.as_view(), name="log_out"),
    path("signup/", views.sign_up, name="sign_up"),
    path("signup-confirm/", views.confirm_signup, name="confirm_sign_up"),
]
