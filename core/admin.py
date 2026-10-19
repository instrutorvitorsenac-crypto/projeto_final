from django.contrib import admin
from .models import (
    ArtistFollow,
    Artwork,
    ArtworkInterest,
    ArtworkLike,
    Profile,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "city", "state", "user")
    list_filter = ("role", "state", "country")
    search_fields = ("name", "user__email", "city")


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    list_display = ("title", "artist", "style", "price", "promotion", "created_at")
    list_filter = ("promotion", "style", "artist__state")
    search_fields = ("title", "artist__name", "description")


admin.site.register((ArtworkLike, ArtistFollow, ArtworkInterest))
