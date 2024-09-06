import jwt
import time
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.settings import SECRET_KEY

from .common import check_authority
from ..serializers import *     # model도 포함


class TableAPIView(APIView):
    def get(self, request, booth_id):
        access_token = request.headers.get('Authorization', None)
        if access_token:
            access_token = access_token.replace('Bearer ', '')
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])  # 토큰 유효 확인
            loaded_booth_id = payload['email']  # 이메일 값
        else:
            temporary_user_id = request.COOKIES.get('temporary_user_id')
            if not temporary_user_id:
                return Response({"message": "인증키가 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)
            try:
                customer = Customer.objects.get(pk=temporary_user_id)
            except Customer.DoesNotExist:
                return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
            serializer = CustomerSerializer(instance=customer)
            data = serializer.data
            if time.time() > data['expire_time']:
                customer.delete()
                return Response({"message": "만료된 인증키입니다."}, status=status.HTTP_401_UNAUTHORIZED)
            loaded_booth_id = data['booth_id']

        if not booth_id == loaded_booth_id:
            return Response({"message": "권한이 없는 부스 입니다."}, status=status.HTTP_403_FORBIDDEN)

        try:
            user_instance = get_object_or_404(User, pk=loaded_booth_id)  # email로 user 정보가 있는지 확인
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        table_items = Table.objects.filter(email=booth_id)
        serializer = TableSerializer(instance=table_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, booth_id):
        if check_authority(request, booth_id):
            try:
                user_instance = get_object_or_404(User, pk=booth_id)
            except Exception as e:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = TableSerializer(data=dict({'email': booth_id}, **request.data))
            if serializer.is_valid(raise_exception=True):
                serializer.create(dict({'email': user_instance}, **request.data))
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                Response({"message": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            Response({"message":"자신의 부스에만 테이블을 추가할 수 있습니다"}, status=status.HTTP_204_NO_CONTENT)


class TableDetailAPIVIew(APIView):
    def get(self, request, booth_id, table_id):
        access_token = request.headers.get('Authorization', None)
        if access_token:
            access_token = access_token.replace('Bearer ', '')
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])  # 토큰 유효 확인
            loaded_booth_id = payload['email']  # 이메일 값
        else:
            temporary_user_id = request.COOKIES.get('temporary_user_id')
            if not temporary_user_id:
                return Response({"message": "인증키가 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)
            try:
                customer = Customer.objects.get(pk=temporary_user_id)
            except Customer.DoesNotExist:
                return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
            serializer = CustomerSerializer(instance=customer)
            data = serializer.data
            if time.time() > data['expire_time']:
                customer.delete()
                return Response({"message": "만료된 인증키입니다."}, status=status.HTTP_401_UNAUTHORIZED)
            loaded_booth_id = data['booth_id']

        if not booth_id == loaded_booth_id:
            return Response({"message": "권한이 없는 부스 입니다."}, status=status.HTTP_403_FORBIDDEN)

        try:
            table_instance = get_object_or_404(Table, pk=table_id)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = TableSerializer(instance=table_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, booth_id, table_id):
        if check_authority(request, booth_id):
            try:
                table_instance = get_object_or_404(Table, pk=table_id)
            except Exception as e:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = TableSerializer(instance=table_instance, data=dict({'email': booth_id}, **request.data))
            if serializer.is_valid(raise_exception=True):
                serializer.save(instance=table_instance)
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                Response({"message": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "권한이 없습니다. 본인 부스의 테이블 정보만 바꿀 수 있습니다."}, status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, booth_id, table_id):
        if check_authority(request, booth_id):
            if Table.objects.count() <= 1 :
                return Response({"message": "테이블은 1개 이상 있어야 합니다"}, status = status.HTTP_409_CONFLICT)
            else:
                try:
                    table_delete_instance = get_object_or_404(Table, pk=table_id)
                except Exception as e:
                    return Response(status=status.HTTP_404_NOT_FOUND)

                table_delete_instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "권한이 없습니다. 본인 부스의 테이블만 삭제할 수 있습니다."}, status=status.HTTP_401_UNAUTHORIZED)
