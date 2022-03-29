from rest_framework import serializers

from .models import BoardGame


class BoardGamesListSerializer(serializers.ModelSerializer):
    """ Пробный сериалайзер для списка игр """

    class Meta:
        model = BoardGame
        fields = "__all__"
