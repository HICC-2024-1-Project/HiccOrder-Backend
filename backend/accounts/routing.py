# myapp/routing.py
from django.urls import path
from .ws_views.staffcall import StaffCallConsumer

websocket_urlpatterns = [
    path('ws/<str:type>/<str:booth_id>/<str:table_id>/', StaffCallConsumer.as_asgi()),
]
