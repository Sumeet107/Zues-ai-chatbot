import json
from channels.generic.websocket import AsyncWebsocketConsumer


# 🔔 Reminder WebSocket Consumer
class ReminderConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.group_name = f"user_{self.scope['user'].id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        print("🔔 Reminder WS Connected")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_reminder(self, event):
        await self.send(text_data=json.dumps({
            "task": event["task"]
        }))


# 🎤 AUDIO STREAM CONSUMER (WebRTC)
class AudioConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()
        print("🎤 Audio Stream Connected")

    async def disconnect(self, close_code):
        print("❌ Audio Stream Disconnected")

    async def receive(self, text_data=None, bytes_data=None):

        # WebRTC sends AUDIO as bytes
        if bytes_data:
            print("📡 Received Audio Chunk")