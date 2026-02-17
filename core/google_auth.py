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
            # Получаем все client IDs
            google_client_ids = self._get_google_client_ids()
            
            # Верифицируем токен в зависимости от того, что прислали
            if id_token_value:
                print("Processing ID token from mobile")
                idinfo = self.verify_id_token(id_token_value, google_client_ids)
            else:
                print("Processing access token from web")
                idinfo = self.verify_access_token(access_token, google_client_ids)
            
            if not idinfo:
                return Response(
                    {'error': 'Failed to verify Google token'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Проверяем email
            email = idinfo.get('email')
            email_verified = idinfo.get('email_verified', False)
            
            if not email:
                return Response(
                    {'error': 'Email not provided by Google'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not email_verified:
                return Response(
                    {'error': 'Email not verified by Google'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Извлекаем информацию о пользователе
            google_id = idinfo['sub']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            picture = idinfo.get('picture', '')
            
            print(f"User info extracted: {email}, {first_name} {last_name}")
            
            # Создаем или получаем пользователя
            user = self._get_or_create_user(
                google_id=google_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                picture=picture
            )
            
            # Генерируем JWT токены
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

        except ValueError as e:
            print(f"ValueError: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Invalid Google token: {str(e)}'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Authentication failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def verify_id_token(self, token, client_ids):
        """Verify Google ID token (used by mobile apps)"""
        try:
            request = google_requests.Request()
            
            # Try each client ID
            for client_id in client_ids:
                try:
                    idinfo = id_token.verify_oauth2_token(
                        token, 
                        request, 
                        audience=client_id
                    )
                    
                    # Check issuer
                    if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                        continue
                    
                    print(f"Successfully verified ID token with client_id: {client_id}")
                    return idinfo
                    
                except Exception as e:
                    print(f"ID token verification failed for client {client_id}: {e}")
                    continue
            
            raise ValueError("ID token verification failed with all client IDs")
            
        except Exception as e:
            print(f"ID token verification error: {e}")
            raise

    def verify_access_token(self, access_token, client_ids):
        """Verify Google access token (used by web)"""
        try:
            # Google's tokeninfo endpoint works with access tokens too
            response = requests.get(
                f'https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}'
            )
            
            if response.status_code == 200:
                token_info = response.json()
                print(f"Access token info: {token_info}")
                
                # Get user info using the access token
                user_info_response = requests.get(
                    'https://www.googleapis.com/oauth2/v3/userinfo',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                
                if user_info_response.status_code == 200:
                    user_info = user_info_response.json()
                    print(f"User info from access token: {user_info}")
                    
                    # Format to match ID token structure
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
                    print(f"Failed to get user info: {user_info_response.status_code}")
                    raise ValueError("Failed to get user info from access token")
            else:
                print(f"Tokeninfo endpoint returned {response.status_code}: {response.text}")
                
                # Alternative method: try to decode JWT if it's a JWT access token
                try:
                    # Some Google access tokens are JWTs
                    unverified = jwt.decode(access_token, options={"verify_signature": False})
                    print(f"Access token as JWT: {unverified}")
                    
                    if unverified.get('iss', '').startswith('accounts.google.com'):
                        # Try to get user info with this token
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
                except Exception as jwt_error:
                    print(f"JWT decode failed: {jwt_error}")
                
                raise ValueError(f"Invalid access token: {response.status_code}")
                
        except Exception as e:
            print(f"Access token verification error: {e}")
            raise

    def _get_google_client_ids(self):
        """Get all valid Google client IDs (web + mobile)"""
        client_ids = []
        
        # Web client ID
        if hasattr(settings, 'GOOGLE_CLIENT_ID'):
            client_ids.append(settings.GOOGLE_CLIENT_ID)
        
        # iOS client ID
        if hasattr(settings, 'GOOGLE_IOS_CLIENT_ID'):
            client_ids.append(settings.GOOGLE_IOS_CLIENT_ID)
        
        # Android client ID
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
            # Link Google account to existing user
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
        
        # Save picture if your model has avatar field
        if picture and hasattr(user, 'avatar'):
            user.avatar = picture
            user.save()
            
        user._is_new_user = True
        return user