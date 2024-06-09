from gdo.base.Logger import Logger
from gdo.base.Thread import Thread


class TelegramThread(Thread):
    _connector: object

    def __init__(self, connector: object):
        super().__init__()
        self._connector = connector

    async def run(self):
        Logger.debug('Running telegram thread.')
        try:
            await self._connector._application.run_polling()
        except RuntimeError:
            raise KeyboardInterrupt
