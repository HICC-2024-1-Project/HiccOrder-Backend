from django.urls import path

from .views import SignAPIView
from .views import AuthAPIView

urlpatterns = [
    path("sign/", SignAPIView.as_view()),   # post-회원 가입, delete-회원 탈퇴
    path("", AuthAPIView.as_view()),   # post - 로그인, delete - 로그아웃, get - 유저정보
]