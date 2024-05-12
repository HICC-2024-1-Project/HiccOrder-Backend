from django.urls import path

from .views import SignAPIView, AuthAPIView, EmailDuplication, BoothAPIView, BoothMenuAPIView, BoothMenuDetailAPIView, \
    TableAPIView, TableDetailAPIVIew, BoothOrderAPIView, TableOrderAPIView, TableOrderControlAPIView

from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("auth/sign/", SignAPIView.as_view()),   # post 회원 가입, delete-회원 탈퇴
    path("auth/", AuthAPIView.as_view()),   # post-로그인, delete-로그아웃, get-유저정보
    path("auth/duplicate/", EmailDuplication.as_view()),  # post-이메일 중복 확인
    path("auth/refresh/", TokenRefreshView.as_view(), name='token_refresh'),     # post-refresh token 재발급
    path("booth/<str:booth_id>/", BoothAPIView.as_view()),
    path("booth/<str:booth_id>/menu/", BoothMenuAPIView.as_view()),
    path("booth/<str:booth_id>/menu/<str:menu_id>/", BoothMenuDetailAPIView.as_view()),
    path("booth/<str:booth_id>/table/", TableAPIView.as_view()),
    path("booth/<str:booth_id>/table/<str:table_id>/", TableDetailAPIVIew.as_view()),
    path("booth/<str:booth_id>/order/", BoothOrderAPIView.as_view()), #전체 주문 목록 확인
    path("booth/<str:booth_id>/order/<str:table_id>/", TableOrderAPIView.as_view()), #테이블 주문 및 주문확인
    path("booth/<str:booth_id>/order/<str:table_id>/<str:order_id>/", TableOrderControlAPIView.as_view()) #주문한 메뉴 수정, 삭제
]
