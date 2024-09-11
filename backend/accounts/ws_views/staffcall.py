from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from channels.db import database_sync_to_async

import json
import time

from ..models import StaffCall, User, Customer
from ..serializers import CustomerSerializer


class StaffCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.booth_id = self.scope['url_route']['kwargs']['booth_id']
        self.type = self.scope['url_route']['kwargs']['type']
        if self.type == 'admin':
            # WebSocket 연결 요청에서 Authorization 헤더 가져오기
            headers = dict(self.scope['headers'])
            token = headers.get(b'Authorization', None)

            if token:
                try:
                    # JWT 토큰을 검증하고 사용자 정보를 가져옵니다.
                    token = token.decode('utf-8').replace('Bearer ', '')
                    access_token = AccessToken(token)
                    email = access_token['email']

                    # 비동기적으로 사용자 정보를 조회
                    user = await self.get_user_by_email(email)

                    if not user.is_authenticated:
                        raise DenyConnection("Invalid token")
                    if not self.booth_id == user.data['email']:
                        raise DenyConnection("Invalid token")

                except Exception as e:
                    raise DenyConnection(f"Authentication failed: {str(e)}")
            else:
                raise DenyConnection("Authorization header missing")
        else:
            self.table_id = self.scope['url_route']['kwargs']['table_id']
            cookies = self.scope.get('cookies', {})
            temporary_user_id = cookies.get('temporary_user_id', None)

            if not temporary_user_id:
                return DenyConnection("인증키가 없습니다.")

            try:
                # 비동기적으로 고객 정보 조회
                customer = await self.get_customer_by_id(temporary_user_id)
            except Customer.DoesNotExist:
                return DenyConnection("권한이 없습니다.")

            serializer = CustomerSerializer(instance=customer)
            data = serializer.data

            if time.time() > data['expire_time']:
                await self.delete_customer(temporary_user_id)
                raise DenyConnection("만료된 인증키입니다.")

            loaded_booth_id = data['booth_id']
            if not self.booth_id == loaded_booth_id:
                raise DenyConnection("권한이 없는 부스 입니다.")

            loaded_table_id = data['table_id']
            if not self.table_id == loaded_table_id:
                raise DenyConnection("권한이 없는 테이블 입니다.")

        self.room_group_name = f'booth_{self.booth_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # 연결 허용
        await self.accept()

        # 클라이언트 연결 시 이전 메시지 전송
        previous_calls = await self.get_previous_calls(self.booth_id)
        for call in previous_calls:
            await self.send(json.dumps({
                'table_id': call.table_id
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self):
        booth_id = self.scope['url_route']['kwargs']['booth_id']
        table_id = self.scope['url_route']['kwargs']['table_id']

        if booth_id and table_id:
            # 메시지를 데이터베이스에 저장
            await self.save_call(booth_id, table_id)

            # 그룹의 모든 클라이언트에게 table_id 전송
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_table_id',
                    'table_id': table_id
                }
            )

    async def send_table_id(self, event):
        table_id = event['table_id']

        # 클라이언트로 table_id 전송
        await self.send(json.dumps({
            'table_id': table_id
        }))

    @database_sync_to_async
    def save_call(self, booth_id, table_id):
        # 데이터베이스에 메시지 저장
        StaffCall.objects.create(
            booth_id=booth_id,
            table_id=table_id,
            timestamp=timezone.now()
        )

    @database_sync_to_async
    def get_previous_calls(self, booth_id):
        # 데이터베이스에서 이전 메시지 가져오기
        return StaffCall.objects.filter(booth_id=booth_id).order_by('timestamp')

    @database_sync_to_async
    def get_user_by_email(self, email):
        # 이메일로 사용자 정보 조회 (비동기 방식)
        return User.objects.get(email=email)

    @database_sync_to_async
    def get_customer_by_id(self, customer_id):
        # 고객 정보 조회 (비동기 방식)
        return Customer.objects.get(pk=customer_id)

    @database_sync_to_async
    def delete_customer(self, customer_id):
        # 고객 정보 삭제 (비동기 방식)
        return Customer.objects.filter(pk=customer_id).delete()
