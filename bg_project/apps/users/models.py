from django.db import models
from django.conf import settings
from bg_project.apps.boardgames.models import BoardGame


class WishList(models.Model):
    user = models.OneToOneField(to=settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,)

    games = models.ManyToManyField(BoardGame, related_name="wish_lists")

    def __str__(self):
        return f"Wishlist пользователя {self.user}"
