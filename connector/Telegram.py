import asyncio

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes

from gdo.base.Application import Application
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.base.Render import Mode
from gdo.core.Connector import Connector
from gdo.core.GDO_Channel import GDO_Channel
from gdo.core.GDO_Session import GDO_Session
from gdo.core.GDO_User import GDO_User
from gdo.telegram.connector.TelegramThread import TelegramThread

import nest_asyncio

nest_asyncio.apply()


class Telegram(Connector):
    _application: object
    _thread: object

    def gdo_connect(self) -> None:
        from gdo.telegram.module_telegram import module_telegram
        mod = module_telegram.instance()
        token = mod.cfg_api_key()
        Logger.debug(f'Connecting to telegram with token {token}')
        self._application = ApplicationBuilder().token(token).build()
        handler = MessageHandler(None, self.handle_telegram_message)
        self._application.add_handler(handler)
        self._thread = TelegramThread(self)
        # asyncio.run(self._thread.run())
        asyncio.get_event_loop_policy().get_event_loop().run_until_complete(self._thread.run())
        # await self._thread.run()
        self._connected = True
        Logger.debug("CONTINUE!")

    async def handle_telegram_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        Logger.debug("Got message")
        try:
            msg = update.edited_message or update.message
            chat = msg.chat
            text = msg.text
            usr = msg.from_user
            user = self._server.get_or_create_user(str(usr.id), usr.username)
            message = Message(text, Mode.TELEGRAM)
            message.env_server(self._server)
            message.env_user(user)
            message.env_session(GDO_Session.for_user(user))
            trigger = self._server.get_trigger()
            if chat.type == ChatType.PRIVATE:
                pass
            else:
                channel = self._server.get_or_create_channel(str(chat.id), chat.title)
                trigger = channel.get_trigger()
                message.env_channel(channel)
            Application.EVENTS.publish('message', message)
            if text.startswith(trigger):
                message._message = message._message[1:]
                await message.execute()
        except Exception as ex:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=str(ex))
            Logger.exception(ex)

    async def send_to_channel(self, message: Message):
        channel = message._env_channel
        text = message._result
        Logger.debug(f"{channel.render_name()} >> {text}")
        try:
            await self._application.bot.send_message(chat_id=int(channel.get_name()), text=text)
        except Exception as ex:
            Logger.exception(ex)

    async def send_to_user(self, message: Message):
        text = message._result
        user = message._env_user
        Logger.debug(f"{user.render_name()} >> {text}")
        try:
            await self._application.bot.send_message(chat_id=int(user.get_name()), text=text)
        except Exception as ex:
            Logger.exception(ex)

