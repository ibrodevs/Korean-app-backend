from django.urls import path
from .views import UpdateUserAPIView,CreateUserAPIView, ListUsers, ListMeAPIView, LogoutAPIView

urlpatterns = [
	path('register/', CreateUserAPIView.as_view(), name='create-user'),
	path('update/<int:pk>', UpdateUserAPIView.as_view(), name='create-user'),
	path('users/', ListUsers.as_view(), name='create-user'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('me/', ListMeAPIView.as_view(), name='user-me')
]
