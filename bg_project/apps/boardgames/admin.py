from django.contrib import admin
from .models import BoardGame


@admin.register(BoardGame)
class BoardGameAdmin(admin.ModelAdmin):
    list_display = ['title', 'release_year', 'bgg_rating', 'photo']
