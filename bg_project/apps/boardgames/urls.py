from django.urls import path
from .views import AllGames

urlpatterns = [
    path('', AllGames.as_view(), name="all_games"),
]
