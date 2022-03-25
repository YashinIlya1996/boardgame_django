from django.urls import path
from .views import AllGames, DetailGame, clear_search_data

urlpatterns = [
    path('clear-search/', clear_search_data, name="clear_search"),
    path('<alias>/', DetailGame.as_view(), name="detail_game"),
    path('', AllGames.as_view(), name="all_games"),
]
