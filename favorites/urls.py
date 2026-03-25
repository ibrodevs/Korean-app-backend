from django.urls import path
from .views import FavoriteListCreateAPIView, FavoriteDeleteAPIView

urlpatterns = [
    path("favorites/", FavoriteListCreateAPIView.as_view(), name="favorites-list-create"),
    path("favorites/<int:product_id>/", FavoriteDeleteAPIView.as_view(), name="favorites-delete"),
]
