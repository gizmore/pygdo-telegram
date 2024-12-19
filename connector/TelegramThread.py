from gdo.base.Thread import Thread


class TelegramThread(Thread):
    _connector: object

    def __init__(self, connector: object):
        super().__init__()
        self._connector = connector

    async def run(self):
        self._connector._application.run_polling(close_loop=False)
