from django.contrib import admin
from .models import WishList, Profile


@admin.register(WishList)
class WishListAdmin(admin.ModelAdmin):
    list_display = ("user",)
    filter_horizontal = ("games", )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    filter_horizontal = ("friendlist", )