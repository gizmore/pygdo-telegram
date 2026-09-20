from typing import TYPE_CHECKING

from telegram import Update

from gdo.base.Application import Application

if TYPE_CHECKING:
    from gdo.telegram.connector.Telegram import  Telegram

class TelegramThread:
    _connector: 'Telegram'

    def __init__(self, connector: 'Telegram'):
        super().__init__()
        self._connector = connector

    async def run(self):
        app = self._connector._application
        await app.initialize()
        await app.start()
        # Telegram excludes chat_member updates from its historical default.
        # Ask explicitly so the connector receives group joins and leaves.
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
