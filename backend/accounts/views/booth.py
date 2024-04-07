import jwt
from django.http import JsonResponse
from rest_framework.views import APIView

from ..serializers import *
from rest_framework import status
from rest_framework.response import Response
from backend.settings import SECRET_KEY


class BoothAPIView(APIView):
    def patch(self, request, booth_id):     # 부스 정보 추가 및 수정
        try:
            access_token = request.headers.get('Authorization', None)
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])    # 토큰 유효 확인
            user = User.objects.get(email=payload['email'])     # 이메일 값으로 유저 확인
        except jwt.exceptions.DecodeError:
            return JsonResponse({'message': 'INVALID_TOKEN'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'message': 'INVALID_USER'}, status=400)
        try:
            instance = User.objects.get(pk=booth_id)

        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if user == instance:    # 토큰의 유저 정보와 유저 정보가 일치할 때만 허가
            serializer = UserSerializer(instance, data=request.data, partial=True)

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            serializer.save(instance=instance)
            return Response({"message": "User updated successfully"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "권한이 없습니다. 자신의 정보만 바꿀 수 있습니다."}, status=status.HTTP_401_UNAUTHORIZED)
