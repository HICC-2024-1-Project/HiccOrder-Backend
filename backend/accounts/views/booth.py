import jwt
from rest_framework.views import APIView

from ..serializers import *
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from backend.settings import SECRET_KEY
from django.shortcuts import get_object_or_404

from .common import get_fields


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
                # serializer.create(dict({'email': booth_id}, **request.data))
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
        access_token = request.headers.get('Authorization', None).replace('Bearer ', '')
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])  # 토큰 유효 확인
        user = User.objects.get(email=payload['email'])  # 이메일 값으로 유저 확인

        user_instance = get_object_or_404(User, pk=booth_id)
        if user == user_instance:  # 토큰의 유저 정보와 유저 정보가 일치할 때만 허가
            booth_menu_instance = get_object_or_404(BoothMenu, pk=menu_id)
            serializer = BoothMenuSerializer(booth_menu_instance, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save(instance=booth_menu_instance)
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                Response({"message": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "권한이 없습니다. 자신의 부스 정보만 바꿀 수 있습니다."}, status=status.HTTP_401_UNAUTHORIZED)
        