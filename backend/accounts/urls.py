from django.urls import path

from .views import SignAPIView, AuthAPIView, EmailDuplication

urlpatterns = [
    path("sign/", SignAPIView.as_view()),   # post 회원 가입, delete-회원 탈퇴
    path("", AuthAPIView.as_view()),   # post-로그인, delete-로그아웃, get-유저정보
    path("duplicate/", EmailDuplication.as_view())  # post-이메일 중복 확인
]
