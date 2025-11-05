from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gdo.telegram.connector.Telegram import  Telegram

class TelegramThread:
    _connector: 'Telegram'

    def __init__(self, connector: 'Telegram'):
        super().__init__()
        self._connector = connector

    def run(self):
        self._connector._application.run_polling(close_loop=False)
