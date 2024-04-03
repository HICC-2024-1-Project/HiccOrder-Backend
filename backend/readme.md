# 개발 환경 설명

## 초기 세팅
- [1. django 초기세팅](https://mons1220.tistory.com/282)
- [2. settings.py secret key 숨기기](https://medium.com/iovsomnium/django-django-secret-key-%EB%B6%84%EB%A6%AC%ED%95%98%EA%B8%B0-74288462e2ff)

## 라이브러리 구성
- python: 3.8 이상
- django
- rest_framework_simplejwt

## app 구성
- api 단위에 맞게 app 구성
- 예를 들어 api/auth/sign-up api를 만드려고 한다면 auth라는 app을 생성하고 그 아래에 생성
  - 현재 실수로 accounts 라고 이름을 생성한 상태, 추후 auth로 수정 예정

## url 구성
- 세부 url도 app에서 생성
- 먼저 backend/urls.py에 해당 app url과 연결
- app에서 url 최종 세팅
```python
# backend/urls.py
base_url = "api/" # 기본 url
urlpatterns = [
    path('admin/', admin.site.urls),
    path(base_url+"auth/", include('accounts.urls')),   # auth
]
```
```python
# accounts/urls.py
from .views import RegisterAPIView  # view에서 api 기능 불러오기

urlpatterns = [
    path("sign-up/", RegisterAPIView.as_view()),   # post-회원 가입
]
```

## 기타 파일 설명
- django는 settings.py 파일 안에 secret key가 있습니다. 보안을 위해 초기 세팅 2를 참고 바랍니다.

## 사용할 tool
- postman
  - api 테스트용 툴