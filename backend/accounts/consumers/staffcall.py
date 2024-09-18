from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from channels.db import database_sync_to_async

from rest_framework_simplejwt.tokens import AccessToken
import json
import time

from ..models import StaffCall, User, Customer
from ..serializers import CustomerSerializer


class StaffCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = None
        self.booth_id = self.scope['url_route']['kwargs']['booth_id']
        self.type = self.scope['url_route']['kwargs']['type']
        if self.type == 'admin':
            # WebSocket 연결 요청에서 Authorization 헤더 가져오기
            headers = dict(self.scope['headers'])
            token = headers.get(b'authorization', None)

            if token:
                try:
                    # JWT 토큰을 검증하고 사용자 정보를 가져옵니다.
                    token = token.decode('utf-8').replace('Bearer ', '')
                    access_token = AccessToken(token)
                    email = access_token['email']
                    # 비동기적으로 사용자 정보를 조회
                    user = await self.get_user_by_email(email)
                    if not user.is_authenticated:
                        raise DenyConnection("Invalid autorization token")

                    if self.booth_id != email:
                        raise DenyConnection("Invalid token")

                except Exception as e:
                    raise DenyConnection(f"Authentication failed: {str(e)}")
            else:
                raise DenyConnection("Authorization header missing")
        else:
            self.table_id = self.scope['url_route']['kwargs']['table_id']
            cookies = self.scope.get('headers', [])
            cookie_header = next((header for header in cookies if header[0] == b'cookie'), None)
            cookie_value = cookie_header[1].decode('utf-8') if cookie_header else None

            # 쿠키 값을 JSON으로 파싱
            temporary_user_id = None
            if cookie_value:
                try:
                    # 쿠키 값이 JSON 형식으로 가정
                    cookie_data = json.loads(cookie_value)
                    # temporal_user_id 추출
                    temporary_user_id = cookie_data.get('temporary_user_id', None)
                except json.JSONDecodeError:
                    return DenyConnection("Bad request")

            if not temporary_user_id:
                return DenyConnection("인증키가 없습니다.")

            try:
                # 비동기적으로 고객 정보 조회
                customer = await self.get_customer_by_id(temporary_user_id)
            except Customer.DoesNotExist:
                return DenyConnection("권한이 없습니다.")

            serializer = CustomerSerializer(instance=customer)
            data = serializer.data
            print(data)

            if time.time() > data['expire_time']:
                await self.delete_customer(temporary_user_id)
                raise DenyConnection("만료된 인증키입니다.")

            loaded_booth_id = data['booth_id']
            if self.booth_id != loaded_booth_id:
                raise DenyConnection("권한이 없는 부스 입니다.")

            loaded_table_id = data['table_id']
            if int(self.table_id) != int(loaded_table_id):
                raise DenyConnection("권한이 없는 테이블 입니다.")

        self.room_group_name = f'booth_{self.booth_id.split("@")[0]}_{self.booth_id.split("@")[1]}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # 연결 허용
        await self.accept()

        if self.type == 'admin':
            # 클라이언트 연결 시 이전 메시지 전송
            previous_calls = await self.get_previous_calls(self.booth_id)

            for call in previous_calls:
                await self.send(json.dumps({
                    "event": "staffCall",
                    "data": {
                        "table_id": call
                    }
                }))

    async def disconnect(self, close_code):
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        booth_id = self.scope['url_route']['kwargs']['booth_id']
        table_id = self.scope['url_route']['kwargs'].get('table_id', None)
        try:
            message = json.loads(text_data)
            event = message.get('event', None)
            data = message.get('data', None)

            # 사용자
            if self.type != 'admin':
                if booth_id and table_id:
                    if event == 'staffCall':
                        # 실제 연결된 url과 요청한 table_id가 안 맞는 경우 에러 처리
                        if not table_id != data['table_id']:
                            await self.send(text_data=json.dumps({
                                'error': 'url table_id and request table_id is not same.'
                            }))

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
            else:
                if event == 'delete':
                    await self.delete_call(booth_id, data['table_id'])
        except json.JSONDecodeError:
            # JSON 형식이 잘못된 경우
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))

    async def send_table_id(self, event):
        if self.type == 'admin':
            table_id = event['table_id']

            # 클라이언트로 table_id 전송
            await self.send(json.dumps({
                "event": "staffCall",
                "data": {
                    "table_id": table_id
                }
            }))

    @database_sync_to_async
    def save_call(self, booth_id, table_id):
        # 데이터베이스에 메시지 저장
        return StaffCall.objects.create(
            booth_id=booth_id,
            table_id=table_id
        )

    @database_sync_to_async
    def delete_call(self, booth_id, table_id):
        return StaffCall.objects.filter(booth_id=booth_id, table_id=table_id).delete()

    @database_sync_to_async
    def get_previous_calls(self, booth_id):
        call_list = []
        previous_calls = StaffCall.objects.filter(booth_id=booth_id).order_by('timestamp')
        for call in previous_calls:
            call_list.append(call.table_id)
        # 데이터베이스에서 이전 메시지 가져오기
        return call_list

    @database_sync_to_async
    def get_user_by_email(self, email):
        # 이메일로 사용자 정보 조회
        return User.objects.get(email=email)

    @database_sync_to_async
    def get_customer_by_id(self, customer_id):
        # 고객 정보 조회
        return Customer.objects.get(pk=customer_id)

    @database_sync_to_async
    def delete_customer(self, customer_id):
        # 고객 정보 삭제
        return Customer.objects.filter(pk=customer_id).delete()
