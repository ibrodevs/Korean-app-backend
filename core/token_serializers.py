from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Token serializer that accepts `email` in the payload."""

    def validate(self, attrs):
        # allow clients to send `email` instead of the configured username field
        # e.g. when USERNAME_FIELD == 'email', SimpleJWT expects 'email' key.
        # If a client sends 'email', ensure the serializer's username_field is set.
        if 'email' in attrs:
            attrs[self.username_field] = attrs.get('email')
    
        data = super().validate(attrs)

        refresh_token = data.pop('refresh')
        access_token = data.pop('access')
        
        custom_data = {
            "tokens": {
                "refresh": refresh_token,
                "access": access_token,
            }, 
            "user": {
                'id': self.user.id,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                # Добавьте фото или телефон, если они нужны
                'photo': self.user.photo.url if self.user.photo else None,
            }
        }

        return custom_data