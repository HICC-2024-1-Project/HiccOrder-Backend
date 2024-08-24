from django.shortcuts import redirect
from django.contrib.auth import authenticate
from ..models import *
from rest_framework.views import APIView
from ..serializers import UserSerializerWithNoPassword, UserSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.response import Response
from django.shortcuts import redirect

import os
from json import JSONDecodeError
from rest_framework import status
from django.http import JsonResponse, HttpResponse
import requests


# 구글 소셜로그인 변수 설정
state = os.environ.get("STATE")
BASE_URL = 'http://localhost:8000/'
GOOGLE_CALLBACK_URI = BASE_URL + 'api/auth/google/callback/'


# 구글 로그인
def google_login(request):
    scope = "https://www.googleapis.com/auth/userinfo.email"
    client_id = os.environ.get("SOCIAL_AUTH_GOOGLE_CLIENT_ID")
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&response_type=code&redirect_uri={GOOGLE_CALLBACK_URI}&scope={scope}")


class GoogleCallbackAPIView(APIView):
    def get(self, request):
        client_id = os.environ.get("SOCIAL_AUTH_GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("SOCIAL_AUTH_GOOGLE_SECRET")
        code = request.GET.get('code')

        # 1. 받은 코드로 구글에 access token 요청
        token_req = requests.post(
            f"https://oauth2.googleapis.com/token?client_id={client_id}&client_secret={client_secret}&code={code}&grant_type=authorization_code&redirect_uri={GOOGLE_CALLBACK_URI}&state={state}")

        ### 1-1. json으로 변환 & 에러 부분 파싱
        token_req_json = token_req.json()
        error = token_req_json.get("error")

        ### 1-2. 에러 발생 시 종료
        if error is not None:
            raise JSONDecodeError(error)

        ### 1-3. 성공 시 access_token 가져오기
        access_token = token_req_json.get('access_token')

        #################################################################

        # 2. 가져온 access_token으로 이메일값을 구글에 요청
        email_req = requests.get(f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}")
        email_req_status = email_req.status_code

        ### 2-1. 에러 발생 시 400 에러 반환
        if email_req_status != 200:
            return JsonResponse({'err_msg': 'failed to get email'}, status=status.HTTP_400_BAD_REQUEST)

        ### 2-2. 성공 시 이메일 가져오기
        email_req_json = email_req.json()
        email = email_req_json.get('email')

        #################################################################

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None
        if user:
            if user.is_oauth:
                # 이미 회원이 존재하는 경우, 로그인을 수행하고 토큰을 발급합니다.
                token = TokenObtainPairSerializer.get_token(user)
                refresh_token = str(token)
                access_token = str(token.access_token)
                response_data = {
                    "user": UserSerializer(user).data,
                    "message": "login success",
                    "token": {
                        "access": access_token,
                        "refresh": refresh_token,
                    },
                }
                response = Response(response_data, status=status.HTTP_200_OK)
                response.set_cookie("access", access_token, httponly=True)
                response.set_cookie("refresh", refresh_token, httponly=True)
                return response
            else:
                return HttpResponse('<script>alert("이미 일반 로그인으로 가입된 계정입니다. 일반 로그인으로 로그인 해주세요."); setTimeout(() => {window.location.href="/auth/login"}, 1000);</script>')
        else:
            # 새로운 회원 가입을 진행합니다.
            data = {"email": email, "password": '', "is_oauth": True}
            serializer = UserSerializerWithNoPassword(data=data)
            if serializer.is_valid():
                user = serializer.save()

                # jwt 토큰 접근
                token = TokenObtainPairSerializer.get_token(user)
                refresh_token = str(token)
                access_token = str(token.access_token)
                response_data = {
                    "user": serializer.data,
                    "message": "register success",
                    "token": {
                        "access": access_token,
                        "refresh": refresh_token,
                    },
                }
                response = Response(response_data, status=status.HTTP_200_OK)
                response.set_cookie("access", access_token, httponly=True)
                response.set_cookie("refresh", refresh_token, httponly=True)
                return response
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
