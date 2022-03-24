from django.urls import path
from .views import AllGames, DetailGame

urlpatterns = [
    path('<alias>/', DetailGame.as_view(), name="detail_game"),
    path('', AllGames.as_view(), name="all_games"),
]
