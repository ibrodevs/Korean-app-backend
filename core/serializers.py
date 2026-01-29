from rest_framework import serializers
from .models import CustomUser

class WriteUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('email', 'gender', 'birth_date', 'photo', 'first_name', 'last_name', 'is_staff', 'is_active', 'password')
        extra_kwargs = {
            'password': {'write_only' : True}
            }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance
    

class ListUsers(serializers.ModelSerializer):
     class Meta:
        model = CustomUser
        fields = ('email', 'gender', 'birth_date', 'photo', 'first_name', 'last_name', 'is_staff', 'is_active', 'password')
        