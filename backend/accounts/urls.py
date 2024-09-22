from django.urls import path


from .views import *


from .views import RefreshView

urlpatterns = [
    path("auth/sign/", SignAPIView.as_view()),   # post 회원 가입, delete-회원 탈퇴
    path("auth/", AuthAPIView.as_view()),   # post-로그인, delete-로그아웃, get-유저정보
    path("auth/duplicate/", EmailDuplication.as_view()),  # post-이메일 중복 확인
    path("auth/refresh/", RefreshView.as_view(), name='token_refresh'),     # post-refresh token 재발급
    path("auth/google/login/", google_login, name='google_login'),
    path("auth/google/callback/", GoogleCallbackAPIView.as_view(), name='google_callback'),
    path("auth/password/", SendVerificationCodeView.as_view()),
    path("auth/password/verify/", VerifyCodeView.as_view()),
    path("auth/qrlink/", GenerateTemporaryLinkAPIView.as_view()),
    path("auth/qrsignin/<str:token>/", TemporaryResourceAPIView.as_view()),
    path("booth/order/", TableOrderAPIView.as_view()),  # 사용자용 테이블 주문 및 주문 확인
    path("booth/<str:booth_id>/order/", BoothOrderAPIView.as_view()),   # 전체 주문 목록 확인
    path("booth/<str:booth_id>/order/<str:table_id>/", TableOrderManagerAPIView.as_view()),  # 관리자용 테이블 주문 및 주문 확인
    path("booth/<str:booth_id>/order/<str:table_id>/<str:order_id>/", TableOrderControlAPIView.as_view()),  # 주문한 메뉴 수정, 삭제, 상태 변경
    path("booth/<str:booth_id>/payment/<str:table_id>/", OrderPaymentAPIView.as_view()),    # 결제
    path("booth/<str:booth_id>/", BoothAPIView.as_view()),
    path("booth/<str:booth_id>/menu/", BoothMenuAPIView.as_view()),
    path("booth/<str:booth_id>/menu/<str:menu_id>/", BoothMenuDetailAPIView.as_view()),
    path("booth/<str:booth_id>/table/", TableAPIView.as_view()),
    path("booth/<str:booth_id>/table/status/", TableStatus.as_view()),
    path("booth/<str:booth_id>/table/<str:table_id>/", TableDetailAPIVIew.as_view()),
    path("s3/booth/<str:booth_id>/", BoothS3APIView.as_view()),
    path("s3/booth/<str:booth_id>/menu/<str:menu_id>/", BoothMenuS3APIView.as_view()),
    path("call/booth/<str:booth_id>/", StaffCallGetAPIView.as_view()),
    path("call/booth/<str:booth_id>/<int:table_id>/", StaffCallAPIView.as_view())
]
