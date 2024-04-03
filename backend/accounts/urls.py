from django.urls import path

from .views import SignAPIView, AuthAPIView, EmailDuplication

from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("sign/", SignAPIView.as_view()),   # post 회원 가입, delete-회원 탈퇴
    path("", AuthAPIView.as_view()),   # post-로그인, delete-로그아웃, get-유저정보
    path("duplicate/", EmailDuplication.as_view()),  # post-이메일 중복 확인
    path("refresh/", TokenRefreshView.as_view(), name='token_refresh'),     # post-refresh token 재발급
]
