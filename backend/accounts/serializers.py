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
        strict = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'initial_data') and self.initial_data:
            # 들어온 데이터의 필드 목록
            incoming_fields = set(self.initial_data.keys())
            # Serializer에 정의된 필드 목록
            defined_fields = set(self.fields.keys())

            # Serializer에 정의되지 않은 필드 확인
            undefined_fields = incoming_fields - defined_fields
            if undefined_fields:
                raise serializers.ValidationError(f"Undefined fields: {', '.join(undefined_fields)}")

    def create(self, validated_data):
        booth_menu = BoothMenu.objects.create_booth_menu(
            email=validated_data['email'],
            category=validated_data['category'],
            menu_name=validated_data['menu_name'],
            price=validated_data['price'],
            description=validated_data['description'],
        )
        return booth_menu
