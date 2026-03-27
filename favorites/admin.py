from django.contrib import admin
from .models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    list_filter = ("created_at",)
    raw_id_fields = ("user", "product")
