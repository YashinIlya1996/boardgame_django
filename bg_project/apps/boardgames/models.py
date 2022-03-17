from django.db import models


class BoardGame(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    tesera_alias = models.SlugField(max_length=70, unique=True)
    description = models.TextField(null=True, blank=True)
    release_year = models.PositiveSmallIntegerField(null=True, blank=True)
    bgg_rating = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)
    tesera_id = models.IntegerField(unique=True)
    avg_game_time = models.PositiveSmallIntegerField(blank=True, null=True)
    min_players_count = models.PositiveSmallIntegerField(blank=True, null=True)
    max_players_count = models.PositiveSmallIntegerField(blank=True, null=True)
    photo = models.ImageField(upload_to='boardgames/main_bg_photo/')

    def __str__(self):
        return f'{self.title}'
