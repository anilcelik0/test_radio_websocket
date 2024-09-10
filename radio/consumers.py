import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .tasks import listen_to_port
import json

class RadioConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "audio_group"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print("WebSocket connected")
        

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print("WebSocket disconnected")
        
    async def receive(self, text_data):
        pass


    async def send_audio_data(self, event):
        data = event['message']
        await self.send(bytes_data=data)
