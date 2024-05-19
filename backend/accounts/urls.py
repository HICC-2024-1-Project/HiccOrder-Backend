from django.urls import path

from .views import *

from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("auth/sign/", SignAPIView.as_view()),   # post 회원 가입, delete-회원 탈퇴
    path("auth/", AuthAPIView.as_view()),   # post-로그인, delete-로그아웃, get-유저정보
    path("auth/duplicate/", EmailDuplication.as_view()),  # post-이메일 중복 확인
    path("auth/refresh/", TokenRefreshView.as_view(), name='token_refresh'),     # post-refresh token 재발급
    path("booth/<str:booth_id>/", BoothAPIView.as_view()),
    path("booth/<str:booth_id>/menu/", BoothMenuAPIView.as_view()),
    path("auth/google/login/", google_login, name='google_login'),
    path("auth/google/callback/", GoogleCallbackAPIView.as_view(), name='google_callback'),
    path("auth/password/", SendVerificationCodeView.as_view()),
    path('auth/password/verify/', VerifyCodeView.as_view()),
]
