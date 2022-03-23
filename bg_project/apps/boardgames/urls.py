from django.urls import path
from . import views

urlpatterns = [
    path('games/', views.AllGames.as_view(), name="all_games"),
    path('', views.index, name="index"),
]
