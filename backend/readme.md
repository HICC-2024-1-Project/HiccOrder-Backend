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

## view 구성
### 파일 구조
- views/__init__에 사용할 코드 등록
- views/파일명.py 형태로 기능별로 구분
- 좀 더 세부적으로 구분이 필요한 경우 views/패키지명(폴더)/__init__, views/패키지명(폴더)/파일명.py로 구성
### view.py 구성
- DRF view 구성에는 크게 [2가지 방식](https://velog.io/@qlgks1/Django-DRF-FBVFunction-Based-Views-vs-CBVClass-Based-Views)이 있습니다.
- 저희는 클래스형을 사용할 예정입니다.
  - 함수형(Function Based View)
    - 장점
      - 편하게 구현 가능
      - 읽기 편한 로직 데코레이터 사용이 명료함
      - 단발성, 재사용 가능성이 낮은 특별한 비즈니스 로직의 API를 작성할 때 유리
    - 단점
      - 1회성 성격이기 때문에 재사용성이 낮고, 상속의 개념이 아니라 확장하기 힘듦
      - 비즈니스 로직에, 익숙한 OOP 디자인패턴을 적용하기 힘듦
      - CRUD를 만들때, 조건문 분기처리를 해서 다 따로 하나하나 처리를 해야한다. 또는 method를 분리하면 같은 모델 대상으로 단순 CRUD만 하더라도 4개의 함수를 작성해야 함
  ```python
  @api_view(['GET'])
  def HelloAPI(request):
    return Response("hello world!")
  ```
  - 클래스형(Class Based View)
    - 장점
      - 확장 / 재사용 용이
      - 다중 상속, Mixin 가능
      - HTTP Method가 클래스 안에서 나누어 처리 강력한 Generic Class View
    - 단점
      - 단순한 요청, 단발성 1회성, 특수한 비즈니스 로직 처리에 상속으로 인해 버려지는 코드가 있다. 그렇기 때문에 필요없는 기능까지 모두 상속받아서 만들어 무거워질 수 있음
  ```python
  class HelloAPI(APIView):
    def get(self, request):
        return Response("hello world!")
  ```

## 기타 파일 설명
- django는 settings.py 파일 안에 secret key가 있습니다. 보안을 위해 초기 세팅 2를 참고 바랍니다.

## 사용할 tool
- postman
  - api 테스트용 툴