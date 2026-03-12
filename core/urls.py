from django.urls import path
from .views import (
    UpdateUserAPIView, CreateUserAPIView, ListUsers,
    ListMeAPIView, LogoutAPIView,
    CartAPIView, CartItemCreateAPIView,
    CartItemUpdateDeleteAPIView, CartClearAPIView,
    CartItemBulkCreateAPIView, CartItemBulkUpdateAPIView, CartItemBulkDeleteAPIView,
)
from .google_auth import GoogleAuthView

urlpatterns = [
	path('register/', CreateUserAPIView.as_view(), name='create-user'),
	path('update/<int:pk>', UpdateUserAPIView.as_view(), name='update-user'),
	path('users/', ListUsers.as_view(), name='list-users'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('me/', ListMeAPIView.as_view(), name='user-me'),
    # Google OAuth
    path('google/', GoogleAuthView.as_view(), name='google-auth'),

    # Cart — single item operations
    path('cart/', CartAPIView.as_view(), name='cart-detail'),
    path('cart/clear/', CartClearAPIView.as_view(), name='cart-clear'),
    path('cart/items/', CartItemCreateAPIView.as_view(), name='cart-item-create'),
    path('cart/items/<int:item_id>/', CartItemUpdateDeleteAPIView.as_view(), name='cart-item-update-delete'),

    # Cart — bulk operations
    path('cart/items/bulk-add/', CartItemBulkCreateAPIView.as_view(), name='cart-item-bulk-add'),
    path('cart/items/bulk-update/', CartItemBulkUpdateAPIView.as_view(), name='cart-item-bulk-update'),
    path('cart/items/bulk-delete/', CartItemBulkDeleteAPIView.as_view(), name='cart-item-bulk-delete'),
]
