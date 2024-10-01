import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connected: {self.room_group_name}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected: {self.room_group_name}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            sender_id = text_data_json['sender_id']
            receiver_id = text_data_json['receiver_id']

            logger.info(f"Received message: {message} from {sender_id} to {receiver_id}")

            # Save message to database
            await self.save_message(sender_id, receiver_id, message)

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': sender_id,
                    'receiver_id': receiver_id
                }
            )
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")

    async def chat_message(self, event):
        try:
            message = event['message']
            sender_id = event['sender_id']
            receiver_id = event['receiver_id']

            sender = await self.get_user(sender_id)

            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'message': message,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'sender_username': sender.username
            }))
            logger.info(f"Sent message to WebSocket: {message}")
        except Exception as e:
            logger.error(f"Error in chat_message: {str(e)}")

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, message):
        try:
            sender = User.objects.get(id=sender_id)
            receiver = User.objects.get(id=receiver_id)
            Message.objects.create(sender=sender, receiver=receiver, content=message)
            logger.info(f"Message saved to database: {message}")
        except Exception as e:
            logger.error(f"Error saving message to database: {str(e)}")

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User with id {user_id} does not exist")
            return None
