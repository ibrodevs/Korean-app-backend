from django.shortcuts import render
from rest_framework import generics
from .serializers import WriteUserSerializer, ListUsers
from rest_framework.permissions import AllowAny

from .models import CustomUser

# Create your views here.
class CreateUserAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = CustomUser.objects.all()
    serializer_class = WriteUserSerializer

class ListUsers(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = CustomUser.objects.all()
    serializer_class = ListUsers
