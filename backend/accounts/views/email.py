from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache
from ..models import User
from django.contrib.auth.hashers import make_password
import random
import string

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.serializers import UserSerializer


def generate_verification_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def send_verification_email(email, verification_code):
    title = "HICC Order 이메일 인증"
    context = {
        'subject_message': '인증번호',
        'content_message': verification_code,
    }
    content = render_to_string('email_template.html', context)
    mail = EmailMessage(title, content, settings.EMAIL_HOST_USER, [email])
    mail.content_subtype = "html"
    mail.send()


class SendVerificationCodeView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_oauth:
            return Response({'error': 'User with this email is an easy login user'}, status=status.HTTP_404_NOT_FOUND)
        verification_code = generate_verification_code()
        # Save the verification code in the cache with a timeout (5 minutes)
        cache.set(email, verification_code, timeout=300)
        send_verification_email(email, verification_code)
        return Response({'message': 'Verification code sent successfully'}, status=status.HTTP_200_OK)


class VerifyCodeView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        verification_code = request.data.get('verify_number')
        password = request.data.get('password')

        if not email or not verification_code or password is None:
            return Response({'error': 'Email and verify numbers are required'}, status=status.HTTP_400_BAD_REQUEST)

        cached_code = cache.get(email)
        if not cached_code:
            return Response({'error': 'Invalid or expired verification code'}, status=status.HTTP_404_NOT_FOUND)
        if cached_code != verification_code:
            return Response({'error': 'Invalid verification_code'}, status=status.HTTP_401_UNAUTHORIZED)

        # 인증 번호 유효만 확인
        if password == '':
            return Response({'message': 'Verification successful'}, status=status.HTTP_200_OK)

        try:
            user = User.objects.get(email=email)
            user.password = make_password(password)
            user.save()
            # JWT 토큰 접근
            token = TokenObtainPairSerializer.get_token(user)
            refresh_token = str(token)
            access_token = str(token.access_token)
            res = Response(
                {
                    "user": UserSerializer(user).data,
                    "message": "Password reset successful",
                    "token": {
                        "access": access_token,
                        "refresh": refresh_token,
                    },
                },
                status=status.HTTP_200_OK,
            )
            # JWT 토큰 => 쿠키에 저장
            res.set_cookie("access", access_token, httponly=True)
            res.set_cookie("refresh", refresh_token, httponly=True)
            return res
        except User.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
