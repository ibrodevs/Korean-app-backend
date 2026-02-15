from rest_framework import serializers
from rest_framework.response import Response
from .models import CustomUser

class WriteUserSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'phone', 'photo', 'first_name', 'last_name', 'password', 'password_confirm')
        extra_kwargs = {
            'password': {'write_only' : True}
            }
    
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('password must be at least 8 characters')
        
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain a capital letter.")
        
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain a digit letter.")
        
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match'
            })
        return attrs
        
    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        instance.set_password(password)
        instance.save()
        return instance
    
    def update(self, instance, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
    

class ListUserSerializer(serializers.ModelSerializer):
     class Meta:
        model = CustomUser
        fields = ('email', 'photo', 'first_name', 'last_name')
        