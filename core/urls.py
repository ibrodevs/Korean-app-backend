from django.urls import path
from .views import CreateUserAPIView, ListUsers

urlpatterns = [
	path('create-user', CreateUserAPIView.as_view(), name='create-user'),
	path('users', ListUsers.as_view(), name='create-user')
]
