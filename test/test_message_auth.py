import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from gdo.telegram.connector.Telegram import Telegram


class TelegramMessageAuthTest(unittest.IsolatedAsyncioTestCase):
    async def test_sender_authentication_is_per_message_and_rejects_anonymous(self):
        for sender_chat, sender_id in ((None, 123), (object(), 123), (None, True), (None, 0)):
            with self.subTest(sender_chat=sender_chat, sender_id=sender_id):
                connector = Telegram()
                connector.get_or_create_dog = AsyncMock()
                connector._server = MagicMock()
                user = MagicMock()
                user.get_displayname.return_value = 'Alice'
                connector._server.get_or_create_user = AsyncMock(return_value=user)
                connector._server.on_user_joined = AsyncMock()
                sender = SimpleNamespace(id=sender_id, username='Alice', full_name='Alice')
                chat = SimpleNamespace(type='private', _bot=MagicMock(), id=123)
                raw = SimpleNamespace(chat=chat, from_user=sender, sender_chat=sender_chat,
                                      photo=[], document=None, text='hello')
                update = SimpleNamespace(edited_message=None, message=raw)
                message = MagicMock()
                message.execute = AsyncMock()
                with patch('gdo.telegram.connector.Telegram.Message', return_value=message), \
                        patch('gdo.telegram.connector.Telegram.Application.tick'), \
                        patch('gdo.telegram.connector.Telegram.Application.mode'), \
                        patch('gdo.telegram.connector.Telegram.Application.set_current_user'), \
                        patch('gdo.telegram.connector.Telegram.Logger.debug'):
                    await connector.handle_telegram_message(update, MagicMock())
                message.platform_identity.assert_called_once_with(sender_id, trusted=sender_chat is None)
                message.execute.assert_awaited_once()

    async def test_senderless_message_is_ignored(self):
        connector = Telegram()
        connector.get_or_create_dog = AsyncMock()
        connector._server = MagicMock()
        raw = SimpleNamespace(chat=SimpleNamespace(_bot=MagicMock()), from_user=None)
        with patch('gdo.telegram.connector.Telegram.Application.tick'), \
                patch('gdo.telegram.connector.Telegram.Application.mode'):
            await connector.handle_telegram_message(SimpleNamespace(edited_message=None, message=raw), MagicMock())
        connector._server.get_or_create_user.assert_not_called()
