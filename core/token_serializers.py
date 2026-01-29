from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Token serializer that accepts `email` in the payload."""

    def validate(self, attrs):
        # allow clients to send `email` instead of the configured username field
        # e.g. when USERNAME_FIELD == 'email', SimpleJWT expects 'email' key.
        # If a client sends 'email', ensure the serializer's username_field is set.
        if 'email' in attrs:
            attrs[self.username_field] = attrs.get('email')
        return super().validate(attrs)
