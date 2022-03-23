from django.contrib import admin
from .models import WishList


@admin.register(WishList)
class WishListAdmin(admin.ModelAdmin):
    list_display = ("user",)
    filter_horizontal = ("games", )