from .models import User, BoothMenu, Table, Order, Payment, Customer, StaffCall
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


class UserSerializerWithNoPassword(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('password',)

    def create(self, validated_data):
        # create_user 대신에 create 메서드를 사용합니다.
        user = User.objects.create(**validated_data)
        return user


class BoothSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'booth_name', 'bank_name', 'banker_name', 'account_number', 'booth_image_url']


class BoothMenuSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False, write_only=True)  # file 필드 추가

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

    def update(self, instance, validated_data):
        file = validated_data.pop('file', None)  # file 필드 제거
        for (key, value) in validated_data.items():
            setattr(instance, key, value)
        if file:
            # 파일 업로드 로직 추가 가능
            pass
        instance.save()
        return instance


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = '__all__'

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
        table = Table.objects.create_table(
            email=validated_data['email'],
            table_name=validated_data['table_name']
        )
        return table

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'id': data['id'],
            'table_name': data['table_name'],
            # 필요한 필드만 선택하여 반환
        }


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'order_id': data['order_id'],
            'table_id': data['table_id'],
            'menu_id': data['menu_id'],
            'timestamp': data['timestamp'],
            'quantity': data['quantity'],
            'state': data['state']
        }


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'initial_data') and self.initial_data:
            incoming_fields = set(self.initial_data.keys())
            defined_fields = set(self.fields.keys())
            undefined_fields = incoming_fields - defined_fields
            if undefined_fields:
                raise serializers.ValidationError(f"Undefined fields: {', '.join(undefined_fields)}")

    def create(self, validated_data):
        payment = Payment.objects.create_payment(
            table_id=validated_data['table_id'],
            email=validated_data['email'],
            menu_id=validated_data['menu_id'],
            timestamp=validated_data['timestamp'],
            price=validated_data['price'],
            quantity=validated_data['quantity']
        )
        return payment


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'initial_data') and self.initial_data:
            incoming_fields = set(self.initial_data.keys())
            defined_fields = set(self.fields.keys())
            undefined_fields = incoming_fields - defined_fields
            if undefined_fields:
                raise serializers.ValidationError(f"Undefined fields: {', '.join(undefined_fields)}")

    def create(self, validated_data):
        customer = Customer.objects.create(
            customer_id=validated_data['customer_id'],
            table_id=validated_data['table_id'],
            booth_id=validated_data['booth_id'],
            expire_time=validated_data['expire_time']
        )
        return customer


class StaffCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffCall
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'initial_data') and self.initial_data:
            incoming_fields = set(self.initial_data.keys())
            defined_fields = set(self.fields.keys())
            undefined_fields = incoming_fields - defined_fields
            if undefined_fields:
                raise serializers.ValidationError(f"Undefined fields: {', '.join(undefined_fields)}")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'booth_id': data['booth_id'],
            'table_id': data['table_id'],
            'timestamp': data['timestamp']
        }

    def create(self, validated_data):
        customer = StaffCall.objects.create(
            booth_id=validated_data['booth_id'],
            table_id=validated_data['table_id']
        )
        return customer
