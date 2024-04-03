from django.urls import path

from .views import SignUpAPIView
from .views import AuthAPIView

urlpatterns = [
    path("sign-up", SignUpAPIView.as_view()),   # post-회원 가입
    path("", AuthAPIView.as_view()),   # post - 로그인, delete - 로그아웃, get - 유저정보
]