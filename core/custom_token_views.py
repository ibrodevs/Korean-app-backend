from rest_framework_simplejwt.views import TokenObtainPairView
from .throttles import LoginRateThrottle


class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_classes =  [LoginRateThrottle]