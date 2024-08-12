import jwt
from django.core import cache
from django.core.cache import cache
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from ..serializers import *     # model도 포함
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from backend.settings import SECRET_KEY
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .common import get_fields, check_authority


class BoothAPIView(APIView):
    permission_classes = [IsAuthenticated]  # 권한 확인 + 토큰 유효성 검사

    def patch(self, request, booth_id):     # 부스 정보 추가 및 수정
        access_token = request.headers.get('Authorization', None).replace('Bearer ', '')
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])  # 토큰 유효 확인
        user = User.objects.get(email=payload['email'])  # 이메일 값으로 유저 확인

        instance = get_object_or_404(User, pk=booth_id)
        if user == instance:    # 토큰의 유저 정보와 유저 정보가 일치할 때만 허가
            serializer = UserSerializer(instance, data=request.data, partial=True)

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            serializer.save(instance=instance)
            return Response({"message": "User updated successfully"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "권한이 없습니다. 자신의 정보만 바꿀 수 있습니다."}, status=status.HTTP_401_UNAUTHORIZED)

    def get(self, request, booth_id):   # 부스 정보 가져오기
        user = get_object_or_404(User, pk=booth_id)
        data = get_fields(user,
                               ['email', 'booth_name', 'bank_name', 'banker_name', 'account_number', 'booth_image_url'])
        return Response(data, status=status.HTTP_200_OK)


class BoothMenuAPIView(APIView):
    permission_classes = [IsAuthenticated]  # 권한 확인 + 토큰 유효성 검사

    def get(self, request, booth_id):
        user = get_object_or_404(User, email=booth_id)
        booth_menu_items = BoothMenu.objects.filter(email=user)
        serializer = BoothMenuSerializer(instance=booth_menu_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, booth_id):
        access_token = request.headers.get('Authorization', None).replace('Bearer ', '')
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])  # 토큰 유효 확인
        user = User.objects.get(email=payload['email'])  # 이메일 값으로 유저 확인

        instance = get_object_or_404(User, pk=booth_id)
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
    permission_classes = [IsAuthenticated]  # 권한 확인 + 토큰 유효성 검사

    def get(self, request, booth_id, menu_id):
        booth_menu = get_object_or_404(BoothMenu, pk=menu_id)
        serializer = BoothMenuSerializer(instance=booth_menu)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, booth_id, menu_id):
        if check_authority(request, booth_id):  # 토큰의 유저 정보와 유저 정보가 일치할 때만 허가
            booth_menu_instance = get_object_or_404(BoothMenu, pk=menu_id)
            serializer = BoothMenuSerializer(instance=booth_menu_instance, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save(instance=booth_menu_instance)
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                Response({"message": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
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

        if authority == True:
            booth_orders = Order.objects.filter(email=booth_id)
            if not booth_orders.exists():
                return Response({"message": "주문 현황을 찾을 수 없음"}, status=status.HTTP_404_NOT_FOUND)

            serializer = OrderSerializer(booth_orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)


class TableOrderAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, booth_id, table_id):
        cookie_token = request.COOKIES.get('temporary_user_id')
        if not cookie_token:
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        temporary_user_id = request.session['temporary_user_id']
        if temporary_user_id != cookie_token:
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        cached_data = cache.get(temporary_user_id)
        if not cached_data:
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        email = cached_data.get('booth_id')
        table_id = cached_data.get('table_id')
        table_orders = Order.objects.filter(table_id=table_id, email_id=email).exclude(state='결제완료') #결제상태로 사용자를 구분
        if not table_orders.exists():
            return Response({"message": "주문 현황을 찾을 수 없음"}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(table_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



    def post(self, request, booth_id, table_id):
        cookie_token = request.COOKIES.get('temporary_user_id')
        if not cookie_token:
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        temporary_user_id = request.session['temporary_user_id']
        if temporary_user_id != cookie_token:
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        cached_data = cache.get(temporary_user_id)
        if not cached_data:
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        email = cached_data.get('booth_id')
        table_id = cached_data.get('table_id')
        state = "주문완료"


        content = request.data.get('content', [])
        orders = []
        for item in content:
            order_data = {
                'table_id': table_id,
                'email': email,
                'menu_id': item.get('menu_id'),
                'timestamp': timezone.now(),
                'quantity': item.get('quantity'),
                'state': state
            }
            serializer = OrderSerializer(data=order_data)
            if serializer.is_valid():  #주문이 유효한 경우 메뉴가 존재확인
                menu_id = item.get('menu_id')
                menu_name = item.get('menu_name')
                if not BoothMenu.objects.filter(pk=menu_id, menu_name=menu_name).exists(): #메뉴가 존재하지 않는 경우 404 응답 반환
                    return Response({"message": "존재하는 메뉴가 아닙니다."}, status=status.HTTP_404_NOT_FOUND)
                serializer.save()
                orders.append(serializer.data)  #생성된 주문을 리스트에 추가
            else:
                return Response({"message": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)

        if orders:
            return Response({"content": orders}, status=status.HTTP_201_CREATED)
        else:  #주문이 하나도 생성되지 않은 경우 잘못된 요청 응답 반환
            return Response({"message": "주문을 생성할 수 없습니다. 잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)


class TableOrderControlAPIView(APIView):
    permission_classes = [IsAuthenticated] #권한 확인 + 토큰 유효성 검사

    def patch(self, request, booth_id, table_id, order_id):
        if check_authority(request, booth_id):  # 토큰의 유저 정보와 유저 정보가 일치할 때만 허가
            order_instance = get_object_or_404(Order, order_id=order_id)
            serializer = OrderSerializer(instance=order_instance, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save(instance=order_instance)
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"message": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "유효하지 않는 주문입니다."}, status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, booth_id, table_id, order_id):
        if check_authority(request, booth_id):
            order_instance = get_object_or_404(Order, order_id=order_id)
            order_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "잘못된 접근입니다."}, status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request, booth_id, table_id, order_id):  # 주문 상태 변경
        if check_authority(request, booth_id):
            orderstate = request.data.get("state")
            if orderstate == "주문완료":
                order_instance = get_object_or_404(Order, order_id=order_id)
                order_instance.state = "조리중"
                order_instance.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            elif orderstate == "조리중":
                order_instance = get_object_or_404(Order, order_id=order_id)
                order_instance.state == "조리완료"
                order_instance.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            elif orderstate == "조리완료":
                order_instance = get_object_or_404(Order, order_id=order_id)
                order_instance.state == "결제완료"
                order_instance.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"message": "잘못된 접근입니다."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"message": "잘못된 접근입니다."}, status=status.HTTP_401_UNAUTHORIZED)
