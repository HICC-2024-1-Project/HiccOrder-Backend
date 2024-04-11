from .models import User, BoothMenu
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for (key, value) in validated_data.items():
            setattr(instance, key, value)
        if password is not None:
            instance.set_password(password)
        instance.save()

        return instance


class BoothSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'booth_name', 'bank_name', 'banker_name', 'account_number', 'booth_image_url']


class BoothMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoothMenu
        fields = '__all__'

    def create(self, validated_data):
        booth_menu = BoothMenu.objects.create_booth_menu(
            email=validated_data['email'],
            category=validated_data['category'],
            menu_name=validated_data['menu_name'],
            price=validated_data['price'],
            description=validated_data['description'],
        )
        return booth_menu
