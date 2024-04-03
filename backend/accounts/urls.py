from django.urls import path

from .views import RegisterAPIView

urlpatterns = [
    path("sign-up/", RegisterAPIView.as_view()),   # post-회원 가입
]