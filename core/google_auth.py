import logging

import jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import requests

from .models import CustomUser

logger = logging.getLogger(__name__)


class GoogleAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth authentication"""
    id_token = serializers.CharField(required=False, help_text="Google ID token from mobile app")
    access_token = serializers.CharField(required=False, help_text="Google access token from web")

    def validate(self, data):
        if not data.get('id_token') and not data.get('access_token'):
            raise serializers.ValidationError("Either id_token or access_token is required")
        return data



class GoogleAuthView(APIView):
    """
    Google OAuth2 Authentication Endpoint

    Accepts either Google ID token (mobile) or access token (web),
    verifies it, and returns JWT tokens for authentication.
    """
    permission_classes = [AllowAny]
    serializer_class = GoogleAuthSerializer

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        id_token_value = serializer.validated_data.get('id_token')
        access_token = serializer.validated_data.get('access_token')

        try:
            google_client_ids = self._get_google_client_ids()

            if id_token_value:
                idinfo = self.verify_id_token(id_token_value, google_client_ids)
            else:
                idinfo = self.verify_access_token(access_token, google_client_ids)

            if not idinfo:
                return Response(
                    {'detail': 'Failed to verify Google token.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            email = idinfo.get('email')
            email_verified = idinfo.get('email_verified', False)

            if not email:
                return Response(
                    {'detail': 'Email not provided by Google.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not email_verified:
                return Response(
                    {'detail': 'Email not verified by Google.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            google_id = idinfo['sub']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            picture = idinfo.get('picture', '')

            user = self._get_or_create_user(
                google_id=google_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                picture=picture
            )

            refresh = RefreshToken.for_user(user)

            return Response({
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'auth_provider': user.auth_provider,
                },
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'is_new_user': getattr(user, '_is_new_user', False),
            })

        except ValueError:
            logger.exception("Google token verification failed")
            return Response(
                {'detail': 'Invalid Google token.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception:
            logger.exception("Google authentication error")
            return Response(
                {'detail': 'Authentication failed.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def verify_id_token(self, token, client_ids):
        """Verify Google ID token (used by mobile apps)"""
        request = google_requests.Request()

        for client_id in client_ids:
            try:
                idinfo = id_token.verify_oauth2_token(
                    token,
                    request,
                    audience=client_id
                )

                if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                    continue

                return idinfo

            except Exception:
                logger.debug("ID token verification failed for client %s", client_id)
                continue

        raise ValueError("ID token verification failed with all client IDs")

    def verify_access_token(self, access_token, client_ids):
        """Verify Google access token (used by web)"""
        response = requests.get(
            'https://www.googleapis.com/oauth2/v3/tokeninfo',
            params={'access_token': access_token}
        )

        if response.status_code == 200:
            token_info = response.json()

            user_info_response = requests.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )

            if user_info_response.status_code == 200:
                user_info = user_info_response.json()

                return {
                    'sub': user_info.get('sub'),
                    'email': user_info.get('email'),
                    'email_verified': user_info.get('email_verified', False),
                    'given_name': user_info.get('given_name', ''),
                    'family_name': user_info.get('family_name', ''),
                    'picture': user_info.get('picture', ''),
                    'iss': 'accounts.google.com',
                    'aud': token_info.get('aud'),
                }
            else:
                raise ValueError("Failed to get user info from access token")
        else:
            # Alternative: try to decode JWT if it's a JWT access token
            try:
                unverified = jwt.decode(access_token, options={"verify_signature": False})

                if unverified.get('iss', '').startswith('accounts.google.com'):
                    user_info_response = requests.get(
                        'https://www.googleapis.com/oauth2/v3/userinfo',
                        headers={'Authorization': f'Bearer {access_token}'}
                    )

                    if user_info_response.status_code == 200:
                        user_info = user_info_response.json()
                        return {
                            'sub': user_info.get('sub'),
                            'email': user_info.get('email'),
                            'email_verified': user_info.get('email_verified', False),
                            'given_name': user_info.get('given_name', ''),
                            'family_name': user_info.get('family_name', ''),
                            'picture': user_info.get('picture', ''),
                            'iss': 'accounts.google.com',
                        }
            except Exception:
                logger.debug("JWT decode fallback failed for access token")

            raise ValueError("Invalid access token")

    def _get_google_client_ids(self):
        """Get all valid Google client IDs (web + mobile)"""
        client_ids = []

        if hasattr(settings, 'GOOGLE_CLIENT_ID'):
            client_ids.append(settings.GOOGLE_CLIENT_ID)

        if hasattr(settings, 'GOOGLE_IOS_CLIENT_ID'):
            client_ids.append(settings.GOOGLE_IOS_CLIENT_ID)

        if hasattr(settings, 'GOOGLE_ANDROID_CLIENT_ID'):
            client_ids.append(settings.GOOGLE_ANDROID_CLIENT_ID)

        if not client_ids:
            raise ValueError('No Google client IDs configured')

        return client_ids

    def _get_or_create_user(self, google_id, email, first_name, last_name, picture=''):
        """
        Get existing user or create a new one.
        """
        # Try to find by google_id first
        try:
            user = CustomUser.objects.get(google_id=google_id)
            user._is_new_user = False
            return user
        except CustomUser.DoesNotExist:
            pass

        # Try to find by email
        try:
            user = CustomUser.objects.get(email=email)
            user.google_id = google_id
            if picture and hasattr(user, 'avatar') and not user.avatar:
                user.avatar = picture
            user.save()
            user._is_new_user = False
            return user
        except CustomUser.DoesNotExist:
            pass

        # Create new user
        user = CustomUser.objects.create_user(
            email=email,
            password=None,
            first_name=first_name,
            last_name=last_name,
            google_id=google_id,
            auth_provider='google',
        )

        if picture and hasattr(user, 'avatar'):
            user.avatar = picture
            user.save()

        user._is_new_user = True
        return user
