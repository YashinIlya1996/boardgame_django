from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views

urlpatterns = [
    path("login/", views.log_in, name="log_in"),
    path("logout/", LogoutView.as_view(), name="log_out"),
    path("signin/", views.sign_up, name="sign_up"),
]