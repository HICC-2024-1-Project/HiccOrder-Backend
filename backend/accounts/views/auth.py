import datetime

import jwt
import time

from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotFound

from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.utils.crypto import get_random_string
from django.shortcuts import redirect

from backend.settings import SECRET_KEY

from ..serializers import *


class SignAPIView(APIView):
    # 회원 가입
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # jwt 토큰 접근
            token = TokenObtainPairSerializer.get_token(user)
            refresh_token = str(token)
            access_token = str(token.access_token)
            res = Response(
                {
                    "user": serializer.data,
                    "message": "register successs",
                    "token": {
                        "access": access_token,
                        "refresh": refresh_token,
                    },
                },
                status=status.HTTP_200_OK,
            )

            # jwt 토큰 => 쿠키에 저장
            res.set_cookie("access", access_token, httponly=True)
            res.set_cookie("refresh", refresh_token, httponly=True)

            return res
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 회원 탈퇴
    def delete(self, request):
        permission_classes = [IsAuthenticated]
        user = request.user
        if user.is_authenticated:  # 인증된 사용자인 경우에만 삭제 작업 수행
            user.delete()
            return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "User is not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)


class AuthAPIView(APIView):
    # 유저 정보 확인
    def get(self, request):
        try:
            # access token을 decode 해서 유저 id 추출 => 유저 식별
            access = request.COOKIES['access']
            payload = jwt.decode(access, SECRET_KEY, algorithms=['HS256'])
            pk = payload.get('user_id')
            user = get_object_or_404(User, pk=pk)
            serializer = UserSerializer(instance=user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except(jwt.exceptions.ExpiredSignatureError):
            # 토큰 만료 시 토큰 갱신
            data = {'refresh': request.COOKIES.get('refresh', None)}
            serializer = TokenRefreshSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                access = serializer.data.get('access', None)
                refresh = serializer.data.get('refresh', None)
                payload = jwt.decode(access, SECRET_KEY, algorithms=['HS256'])
                pk = payload.get('user_id')
                user = get_object_or_404(User, pk=pk)
                serializer = UserSerializer(instance=user)
                res = Response(serializer.data, status=status.HTTP_200_OK)
                res.set_cookie('access', access)
                res.set_cookie('refresh', refresh)
                return res
            raise jwt.exceptions.InvalidTokenError

        except(jwt.exceptions.InvalidTokenError):
            # 사용 불가능한 토큰일 때
            return Response(status=status.HTTP_400_BAD_REQUEST)

    # 로그인
    def post(self, request):
        # 유저 인증
        user = authenticate(
            email=request.data.get("email"), password=request.data.get("password")
        )
        # 이미 회원가입 된 유저일 때
        if user is not None:
            serializer = UserSerializer(user)
            # jwt 토큰 접근
            token = TokenObtainPairSerializer.get_token(user)
            refresh_token = str(token)
            access_token = str(token.access_token)
            res = Response(
                {
                    "user": serializer.data,
                    "message": "login success",
                    "token": {
                        "access": access_token,
                        "refresh": refresh_token,
                    },
                },
                status=status.HTTP_200_OK,
            )
            # jwt 토큰 => 쿠키에 저장
            res.set_cookie("access", access_token, httponly=True)
            res.set_cookie("refresh", refresh_token, httponly=True)
            return res
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    # 로그아웃
    def delete(self, request):
        # 쿠키에 저장된 토큰 삭제 => 로그아웃 처리
        response = Response({
            "message": "Logout success"
            }, status=status.HTTP_202_ACCEPTED)
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        return response


class EmailDuplication(APIView):
    # 이메일 중복 확인
    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 이메일을 가진 사용자 수를 확인
        user_count = User.objects.filter(email=email).count()

        if user_count >= 1:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


class GenerateTemporaryLinkAPIView(APIView):
    permission_classes = [IsAuthenticated]  # 권한 확인 + 토큰 유효성 검사

    def get(self, request, *args, **kwargs):
        access_token = request.headers.get('Authorization', None).replace('Bearer ', '')
        # 토큰으로 user 정보 확인
        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])  # 토큰 유효 확인
            user = User.objects.get(email=payload['email'])  # 이메일 값으로 유저 확인

            table_id = request.data['table_id']
        except User.DoesNotExist:
            raise NotFound('Token not found')
        # 유저 정보에서 이메일만 사용
        expire_time = int(time.time()) + 300  # 유효기간 5분 (300초)
        token = get_random_string(20)

        cache.set(token, {'expire_time': expire_time, 'booth_id': user.email, 'table_id': table_id}, timeout=300)  # 캐시에 5분 동안 저장

        temporary_url = request.build_absolute_uri('/api/auth/qrsignin/' + token + '/')  # URL 직접 작성
        print(temporary_url)
        return Response({'temporary_url': temporary_url}, status=status.HTTP_200_OK)


class TemporaryResourceAPIView(APIView):
    def get(self, request, token, *args, **kwargs):
        cached_data = cache.get(token)

        if not cached_data:
            raise PermissionDenied('Link is invalid or expired')

        expire_time = cached_data['expire_time']
        if time.time() > expire_time:
            raise PermissionDenied('Link has expired')
        # 캐시에서 정보를 제거하여 링크가 한 번만 사용되도록 함
        cache.delete(token)
        # 새로운 토큰 생성
        token = get_random_string(20)

        # 세션에 임시 ID 저장
        cache.set(token, {'expire_time': expire_time,
                          'booth_id': cached_data['booth_id'],
                          'table_id': cached_data['table_id']},
                  timeout=6000)  # 캐시에 100분 동안 저장

        # 쿠키에 임시 세션 ID 설정
        response = redirect('/frontend-page/')
        response.set_cookie('temporary_user_id', token, max_age=6000)  # 쿠키 유효기간 100분

        # 리소스에 접근하는 로직 추가
        return response


class RefreshView(APIView):
    # 토큰 재발급
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is missing"}, status=status.HTTP_400_BAD_REQUEST)

        data = {"refresh": refresh_token}
        serializer = TokenRefreshSerializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)
            token = serializer.validated_data
            now = datetime.datetime.now().isoformat()
            res = Response(
                {
                    "timestamp": now,
                    "token": {
                        "access": token['access']
                    },
                    "success": "true"
                },
                status=status.HTTP_200_OK
            )
            return res
        except TokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidToken as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
