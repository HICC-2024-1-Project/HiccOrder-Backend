from ..serializers import *     # model도 포함
from rest_framework import status
from rest_framework.response import Response

from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .common import check_authority


class TableAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, booth_id):
        user_instance = get_object_or_404(User, pk=booth_id)    # email로 user 정보가 있는지 확인
        table_items = Table.objects.filter(email=booth_id)
        serializer = TableSerializer(instance=table_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, booth_id):
        if check_authority(request, booth_id):
            user_instance = get_object_or_404(User, pk=booth_id)
            serializer = TableSerializer(data=dict({'email': booth_id}, **request.data))
            if serializer.is_valid(raise_exception=True):
                serializer.create(dict({'email': user_instance}, **request.data))
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                Response({"message": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            Response({"message":"자신의 부스에만 테이블을 추가할 수 있습니다"}, status=status.HTTP_204_NO_CONTENT)


class TableDetailAPIVIew(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, booth_id, table_id):
        table_instance = get_object_or_404(Table, pk=table_id)
        serializer = TableSerializer(instance=table_instance)
        return Response(serializer.data, status = status.HTTP_200_OK)

    def patch(self, request, booth_id, table_id):
        if check_authority(request, booth_id):
            table_instance = get_object_or_404(Table, pk=table_id)
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
            if Table.objects.count() == 1 :
                return Response({"message": "테이블은 1개 이상 있어야 합니다"}, status = status.HTTP_409_CONFLICT)
            else :
                table_delete_instance = Table.objects.get(id = table_id)
                table_delete_instance.delete()
                return Response(status = status.HTTP_204_NO_CONTENT)
