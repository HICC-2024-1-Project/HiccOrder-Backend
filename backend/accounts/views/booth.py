import jwt
import boto3
import uuid
from datetime import datetime
import time

from django.shortcuts import get_object_or_404, get_list_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from backend.settings import SECRET_KEY, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME, IMAGE_URL


from ..serializers import *     # model도 포함
from .common import get_fields, check_authority, resizeImage


class StaffCallGetAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, booth_id):
        if not check_authority(request, booth_id):
            return Response({"message": "본인 부스만 변경할 수 있습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        call_object_list = StaffCall.objects.filter(booth_id=booth_id)

        table_id = []
        for call_object in call_object_list:
            if StaffCallSerializer(instance=call_object).data['table_id'] not in table_id:
                table_id.append(StaffCallSerializer(instance=call_object).data['table_id'])
            else:
                call_object.delete()
        return Response(table_id, status=status.HTTP_200_OK)


class StaffCallAPIView(APIView):
    def post(self, request, booth_id, table_id):
        temporary_user_id = request.COOKIES.get('temporary_user_id')
        if not temporary_user_id:
            return Response({"message": "인증키가 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            customer = Customer.objects.get(pk=temporary_user_id)
        except Customer.DoesNotExist:
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        serializer = CustomerSerializer(instance=customer)
        data = serializer.data
        if time.time() > data['expire_time']:
            customer.delete()
            return Response({"message": "만료된 인증키입니다."}, status=status.HTTP_401_UNAUTHORIZED)
        loaded_booth_id = data['booth_id']

        if not booth_id == loaded_booth_id:
            return Response({"message": "권한이 없는 부스 입니다."}, status=status.HTTP_403_FORBIDDEN)

        loaded_table_id = data['table_id']
        if not table_id == loaded_table_id:
            return Response({"message": "권한이 없는 테이블 입니다."}, status=status.HTTP_403_FORBIDDEN)

        data = {
            "booth_id": booth_id,
            "table_id": table_id
        }
        serializer = StaffCallSerializer(data=data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.create(serializer.validated_data)
        return Response({"message": "StaffCall updated successfully"}, status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, booth_id, table_id):
        if not check_authority(request, booth_id):
            return Response({"message": "본인 부스만 변경할 수 있습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            call_objects = get_list_or_404(StaffCall, booth_id=booth_id, table_id=table_id)
        except Exception as e:
            return Response({"message": "해당 호출을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        for call_object in call_objects:
            call_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BoothS3APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booth_id):
        if not check_authority(request, booth_id):
            return Response({"message": "본인 부스만 변경할 수 있습니다."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            instance = get_object_or_404(User, pk=booth_id)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        file = request.FILES.get('file')
        if not file:
            return Response({"message": "파일이 없거나, 올바르지 않은 파일입니다."}, status=status.HTTP_400_BAD_REQUEST)

        if file.size > 50 * 1024 * 1024:
            return Response({"message": "파일 크기가 너무 큽니다."}, status=status.HTTP_403_FORBIDDEN)

        image = resizeImage(file)
        if not image:
            return Response({"message": "올바르지 않은 파일입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 이전 이미지 삭제
        s3r = boto3.resource('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        if instance.booth_image_url:
            # 기존 이미지의 S3 key 추출 (이미지 URL에서 경로만 가져옴)
            old_image_key = instance.booth_image_url.replace(IMAGE_URL, '')
            s3r.Bucket(AWS_STORAGE_BUCKET_NAME).Object(old_image_key).delete()

        key = "%s" % (booth_id)
        file._set_name(str(uuid.uuid4()))
        s3r.Bucket(AWS_STORAGE_BUCKET_NAME).put_object(Key=key + '/%s' % (file.name), Body=image,
                                                       ContentType='image/jpeg')
        image_url = IMAGE_URL + "%s/%s" % (booth_id, file.name)
        instance.booth_image_url = image_url
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BoothMenuS3APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booth_id, menu_id):
        if not check_authority(request, booth_id):
            return Response({"message": "권한이 없는 부스입니다."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            menu_instance = get_object_or_404(BoothMenu, pk=menu_id)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        file = request.FILES.get('file')
        if not file:
            return Response({"message": "파일이 없거나, 올바르지 않은 파일입니다."}, status=status.HTTP_400_BAD_REQUEST)

        if file.size > 50 * 1024 * 1024:
            return Response({"message": "파일 크기가 너무 큽니다."}, status=status.HTTP_403_FORBIDDEN)

        image = resizeImage(file)
        if not image:
            return Response({"message": "올바르지 않은 파일입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 이전 이미지 삭제
        s3r = boto3.resource('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        if menu_instance.menu_image_url:
            # 기존 이미지의 S3 key 추출 (이미지 URL에서 경로만 가져옴)
            old_image_key = menu_instance.menu_image_url.replace(IMAGE_URL, '')
            s3r.Bucket(AWS_STORAGE_BUCKET_NAME).Object(old_image_key).delete()

        key = "%s" % (menu_id)
        file._set_name(str(uuid.uuid4()))
        s3r.Bucket(AWS_STORAGE_BUCKET_NAME).put_object(Key=key + '/%s' % (file.name), Body=image,
                                                       ContentType='image/jpeg')
        image_url = IMAGE_URL + "%s/%s" % (menu_id, file.name)
        menu_instance.menu_image_url = image_url
        menu_instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BoothAPIView(APIView):
    # permission_classes = [IsAuthenticated]  # 권한 확인 + 토큰 유효성 검사

    def patch(self, request, booth_id):     # 부스 정보 추가 및 수정
        access_token = request.headers.get('Authorization', None).replace('Bearer ', '')
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])  # 토큰 유효 확인
        user = User.objects.get(email=payload['email'])  # 이메일 값으로 유저 확인

        try:
            instance = get_object_or_404(User, pk=booth_id)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if user == instance:
            data = request.data.copy()

            serializer = UserSerializer(instance, data=data, partial=True)

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            serializer.save(instance=instance)
            return Response({"message": "User updated successfully"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "권한이 없습니다. 자신의 정보만 바꿀 수 있습니다."}, status=status.HTTP_401_UNAUTHORIZED)

    def get(self, request, booth_id):   # 부스 정보 가져오기
        access_token = request.headers.get('Authorization', None)
        if access_token:
            access_token = access_token.replace('Bearer ', '')
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])  # 토큰 유효 확인
            loaded_booth_id = payload['email']  # 이메일 값
        else:
            temporary_user_id = request.COOKIES.get('temporary_user_id')
            if not temporary_user_id:
                return Response({"message": "인증키가 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                customer = Customer.objects.get(pk=temporary_user_id)
            except Customer.DoesNotExist:
                return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
            serializer = CustomerSerializer(instance=customer)
            data = serializer.data
            if time.time() > data['expire_time']:
                customer.delete()
                return Response({"message": "만료된 인증키입니다."}, status=status.HTTP_401_UNAUTHORIZED)
            loaded_booth_id = data['booth_id']

        if not booth_id == loaded_booth_id:
            return Response({"message": "권한이 없는 부스 입니다."}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = get_object_or_404(User, pk=booth_id)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = get_fields(user,
                          ['email', 'booth_name', 'bank_name', 'banker_name', 'account_number', 'booth_image_url'])
        return Response(data, status=status.HTTP_200_OK)


class BoothMenuAPIView(APIView):
    # permission_classes = [IsAuthenticated]  # 권한 확인 + 토큰 유효성 검사

    def get(self, request, booth_id):
        access_token = request.headers.get('Authorization', None)
        if access_token:
            access_token = access_token.replace('Bearer ', '')
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])  # 토큰 유효 확인
            loaded_booth_id = payload['email']  # 이메일 값
        else:
            temporary_user_id = request.COOKIES.get('temporary_user_id')
            if not temporary_user_id:
                return Response({"message": "인증키가 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                customer = Customer.objects.get(pk=temporary_user_id)
            except Customer.DoesNotExist:
                return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
            serializer = CustomerSerializer(instance=customer)
            data = serializer.data
            if time.time() > data['expire_time']:
                customer.delete()
                return Response({"message": "만료된 인증키입니다."}, status=status.HTTP_401_UNAUTHORIZED)
            loaded_booth_id = data['booth_id']

        if not booth_id == loaded_booth_id:
            return Response({"message": "권한이 없는 부스 입니다."}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = get_object_or_404(User, pk=booth_id)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        booth_menu_items = BoothMenu.objects.filter(email=user)
        serializer = BoothMenuSerializer(instance=booth_menu_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, booth_id):
        access_token = request.headers.get('Authorization', None).replace('Bearer ', '')
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])  # 토큰 유효 확인
        user = User.objects.get(email=payload['email'])  # 이메일 값으로 유저 확인

        try:
            instance = get_object_or_404(User, pk=booth_id)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if user == instance:  # 토큰의 유저 정보와 유저 정보가 일치할 때만 허가
            serializer = BoothMenuSerializer(data=dict({'email': booth_id}, **request.data))
            if serializer.is_valid(raise_exception=True):
                serializer.create(dict({'email': instance}, **request.data))
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                Response({"message": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "권한이 없습니다. 자신의 부스 정보만 바꿀 수 있습니다."}, status=status.HTTP_401_UNAUTHORIZED)


class BoothMenuDetailAPIView(APIView):
    # permission_classes = [IsAuthenticated]  # 권한 확인 + 토큰 유효성 검사

    def get(self, request, booth_id, menu_id):
        access_token = request.headers.get('Authorization', None)
        if access_token:
            access_token = access_token.replace('Bearer ', '')
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])  # 토큰 유효 확인
            loaded_booth_id = payload['email']  # 이메일 값
        else:
            temporary_user_id = request.COOKIES.get('temporary_user_id')
            if not temporary_user_id:
                return Response({"message": "인증키가 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)
            try:
                customer = Customer.objects.get(pk=temporary_user_id)
            except Customer.DoesNotExist:
                return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
            serializer = CustomerSerializer(instance=customer)
            data = serializer.data
            if time.time() > data['expire_time']:
                customer.delete()
                return Response({"message": "만료된 인증키입니다."}, status=status.HTTP_401_UNAUTHORIZED)
            loaded_booth_id = data['booth_id']

        if not booth_id == loaded_booth_id:
            return Response({"message": "권한이 없는 부스 입니다."}, status=status.HTTP_403_FORBIDDEN)

        try:
            booth_menu = get_object_or_404(BoothMenu, pk=menu_id, email=loaded_booth_id)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = BoothMenuSerializer(instance=booth_menu)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, booth_id, menu_id):
        if check_authority(request, booth_id):  # 토큰의 유저 정보와 유저 정보가 일치할 때만 허가
            try:
                booth_menu_instance = get_object_or_404(BoothMenu, pk=menu_id)
            except Exception as e:
                return Response(status=status.HTTP_404_NOT_FOUND)

            data = request.data.copy()

            serializer = BoothMenuSerializer(instance=booth_menu_instance, data=data, partial=True)

            if serializer.is_valid(raise_exception=True):
                serializer.save(instance=booth_menu_instance)
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"message": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "권한이 없습니다. 자신의 부스 정보만 바꿀 수 있습니다."}, status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, booth_id, menu_id):
        if check_authority(request, booth_id):
            model = BoothMenu.objects.get(id=menu_id)
            model.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "권한이 없습니다. 자신의 부스 메뉴만 삭제할 수 있습니다."}, status=status.HTTP_401_UNAUTHORIZED)


class BoothOrderAPIView(APIView):
    permission_classes = [IsAuthenticated] #권한 확인 + 토큰 유효성 검사

    def get(self, request, booth_id):
        authority = check_authority(request, booth_id)

        if not authority:
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        # page = request.GET.get('page')
        # size = request.GET.get('size')
        #
        # if not page or not size:
        #     return Response({"message": "page 혹은 size가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        booth_orders = Order.objects.filter(email=booth_id)
        paid_orders = Payment.objects.filter(email=booth_id)

        order_serializer = OrderSerializer(booth_orders, many=True)
        paid_serializer = PaymentSerializer(paid_orders, many=True)

        data = order_serializer.data + paid_serializer.data

        p = sorted(data, key=lambda x: datetime.fromisoformat(x['timestamp']), reverse=True)

        return Response(order_serializer.data + paid_serializer.data, status=status.HTTP_200_OK)


class TableOrderAPIView(APIView):
    def get(self, request):
        temporary_user_id = request.COOKIES.get('temporary_user_id')
        if not temporary_user_id:
            return Response({"message": "인증키가 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            customer = Customer.objects.get(pk=temporary_user_id)
        except Customer.DoesNotExist:
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        serializer = CustomerSerializer(instance=customer)
        data = serializer.data
        if time.time() > data['expire_time']:
            customer.delete()
            return Response({"message": "만료된 인증키입니다."}, status=status.HTTP_401_UNAUTHORIZED)

        booth_id = data['booth_id']
        table_id = data['table_id']

        table_orders = Order.objects.filter(table_id=table_id, email_id=booth_id).exclude(state='결제완료') # 결제상태로 사용자를 구분

        serializer = OrderSerializer(table_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        temporary_user_id = request.COOKIES.get('temporary_user_id')
        if not temporary_user_id:
            return Response({"message": "인증키가 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            customer = Customer.objects.get(pk=temporary_user_id)
        except Customer.DoesNotExist:
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        serializer = CustomerSerializer(instance=customer)
        data = serializer.data
        if time.time() > data['expire_time']:
            customer.delete()
            return Response({"message": "만료된 인증키입니다."}, status=status.HTTP_401_UNAUTHORIZED)

        booth_id = data['booth_id']
        table_id = data['table_id']

        content = request.data.get('content', [])
        serializers = []
        orders = []
        for item in content:
            order_data = {
                'table_id': table_id,
                'email': booth_id,
                'menu_id': item.get('menu_id'),
                'timestamp': timezone.now(),
                'quantity': item.get('quantity'),
                'state': "주문완료"
            }
            serializer = OrderSerializer(data=order_data)
            if serializer.is_valid():  # 주문이 유효한 경우 메뉴가 존재확인
                menu_id = item.get('menu_id')
                if not BoothMenu.objects.filter(pk=menu_id).exists():  # 메뉴가 존재하지 않는 경우 404 응답 반환
                    return Response({"message": "존재하는 메뉴가 아닙니다."}, status=status.HTTP_404_NOT_FOUND)
                serializers.append(serializer)
            else:
                return Response({"message": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)

        for serializer in serializers:
            serializer.save()
            orders.append(serializer.data)  # 생성된 주문을 리스트에 추가
        return Response({"content": orders}, status=status.HTTP_201_CREATED)


class TableOrderManagerAPIView(APIView):
    permission_classes = [IsAuthenticated]  # 권한 확인 + 토큰 유효성 검사

    def get(self, request, booth_id, table_id):
        authority = check_authority(request, booth_id)
        if not authority:
            return Response({"message: 권한이 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)
        table_orders = Order.objects.filter(table_id=table_id, email_id=booth_id).exclude(state='결제완료')  # 결제상태로 사용자를 구분

        serializer = OrderSerializer(table_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, booth_id, table_id):
        content = request.data.get('content', [])
        serializers = []
        orders = []
        for item in content:
            order_data = {
                'table_id': table_id,
                'email': booth_id,
                'menu_id': item.get('menu_id'),
                'timestamp': timezone.now(),
                'quantity': item.get('quantity'),
                'state': "주문완료"
            }
            serializer = OrderSerializer(data=order_data)
            if serializer.is_valid():  # 주문이 유효한 경우 메뉴가 존재확인
                menu_id = item.get('menu_id')
                if not BoothMenu.objects.filter(pk=menu_id).exists():  # 메뉴가 존재하지 않는 경우 404 응답 반환
                    return Response({"message": "존재하는 메뉴가 아닙니다."}, status=status.HTTP_404_NOT_FOUND)
                serializers.append(serializer)
            else:
                return Response({"message": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)

        for serializer in serializers:
            serializer.save()
            orders.append(serializer.data)  # 생성된 주문을 리스트에 추가
        return Response({"content": orders}, status=status.HTTP_201_CREATED)


class TableOrderControlAPIView(APIView):
    permission_classes = [IsAuthenticated]  # 권한 확인 + 토큰 유효성 검사

    def patch(self, request, booth_id, table_id, order_id):
        authority = check_authority(request, booth_id)

        if authority:
            try:
                order_instance = get_object_or_404(Order, order_id=order_id)
            except Exception as e:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = OrderSerializer(instance=order_instance, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save(instance=order_instance)
                return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"message": "권한이 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, booth_id, table_id, order_id):
        authority = check_authority(request, booth_id)

        if authority:
            try:
                order_instance = get_object_or_404(Order, order_id=order_id)
            except Exception as e:
                return Response(status=status.HTTP_404_NOT_FOUND)

            order_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"message":"권한이 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request, booth_id, table_id, order_id):  # 주문 상태 변경
        authority = check_authority(request, booth_id)

        if authority:
            order_state = request.data.get("state")
            try:
                order_instance = get_object_or_404(Order, order_id=order_id)
            except Exception as e:
                return Response(status=status.HTTP_404_NOT_FOUND)

            order_instance.state = order_state
            order_instance.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"message": "권한이 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)


class OrderPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booth_id, table_id):
        if not check_authority(request, booth_id):
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            orders = Order.objects.filter(table_id=table_id, email=booth_id)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        calls = StaffCall.objects.filter(booth_id=booth_id, table_id=table_id)

        menu_prices = []
        valid_orders = []
        # 전부 조리완료 상태인지 확인, 메뉴 총 가격 저장
        for order in orders:
            if order.state in ["주문완료", "조리시작", "조리완료"]:
                return Response({"message": "아직 처리가 완료되지 않은 품목이 있습니다."}, status=status.HTTP_409_CONFLICT)

            # 취소 주문은 처리 안 함
            if order.state != "취소":
                menu = order.menu_id
                menu_prices.append(menu.price)
                valid_orders.append(order)

        # 취소 주문만 있을 경우 정상 처리
        if not valid_orders:
            return Response(status=status.HTTP_204_NO_CONTENT)

        # serializer를 여러개 생성하고 문제가 있는지 확인
        serializers = []
        for i, order in enumerate(valid_orders):
            total_price = 0
            total_price += menu_prices[i] * order.quantity
            serializer = PaymentSerializer(data=dict({'table_id': table_id,
                                                      'email': booth_id,
                                                      'menu_id': order.menu_id.id,
                                                      'timestamp': timezone.now(),
                                                      'price': total_price,
                                                      'quantity': order.quantity}))
            serializers.append(serializer)

        table_fee = request.data.get('table_fee', 0)

        customers = Customer.objects.filter(booth_id=booth_id)
        total_time = 0.0
        for customer in customers:
            expire_time = CustomerSerializer(customer).data['expire_time']
            start_time = int(expire_time) - 18000
            table_time = (int(time.time()) - start_time) / 60
            if total_time < table_time:
                total_time = table_time

        time_serializer = TimeSerializer(data=dict({'booth_id': booth_id,
                                                    'table_id': table_id,
                                                    'table_fee': table_fee,
                                                    'using_time': total_time}))

        if not time_serializer.is_valid(raise_exception=True):
            return Response({'message': "serializer.errors"}, status=status.HTTP_400_BAD_REQUEST)

        # 생성한 serializer가 유효한지 확인
        for serializer in serializers:
            if not serializer.is_valid(raise_exception=True):
                return Response({'message': "serializer.errors"}, status=status.HTTP_400_BAD_REQUEST)

        time_serializer.save()

        # 생성한 serializer를 활용해 값 저장
        for serializer in serializers:
            serializer.save()

        # 주문 기록 전부 지우기
        orders.delete()

        # 호출 기록 전부 지우기
        for call in calls:
            call.delete()

        # 관련 토큰 삭제
        customer = Customer.objects.filter(booth_id=booth_id, table_id=table_id)
        customer.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
