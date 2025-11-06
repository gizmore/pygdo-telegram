from typing import TYPE_CHECKING

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
        while Application.RUNNING:
            app.run_polling()
