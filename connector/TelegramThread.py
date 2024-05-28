import asyncio
import threading
import time

from gdo.base.Application import Application
from gdo.base.Logger import Logger
from gdo.base.Thread import Thread


class TelegramThread(Thread):
    _connector: object

    def __init__(self, connector: object):
        super().__init__()
        self._connector = connector

    async def run(self):
        Logger.debug('Running telegram thread.')
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        try:
            await self._connector._application.run_polling()
            # await self._connector._application.run_polling()
        except RuntimeError:
            raise KeyboardInterrupt
