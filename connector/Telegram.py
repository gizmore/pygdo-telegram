import asyncio

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes

from gdo.base.Application import Application
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.base.Render import Mode
from gdo.core.Connector import Connector
from gdo.core.GDO_Session import GDO_Session
from gdo.core.GDO_User import GDO_User
from gdo.telegram.connector.TelegramThread import TelegramThread

class Telegram(Connector):
    _application: object
    _thread: TelegramThread

    def get_render_mode(self) -> Mode:
        return Mode.TELEGRAM

    def gdo_connect(self) -> None:
        from gdo.telegram.module_telegram import module_telegram
        mod = module_telegram.instance()
        token = mod.cfg_api_key()
        Logger.debug(f'Connecting to telegram with token {token}')
        self._application = ApplicationBuilder().token(token).build()
        handler = MessageHandler(None, self.handle_telegram_message)
        self._application.add_handler(handler)
        self._thread = TelegramThread(self)
        asyncio.create_task(self._thread.run())
        self._connected = True

    async def handle_telegram_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.edited_message or update.message
        try:
            Application.tick()
            Application.mode(Mode.TELEGRAM)
            chat = msg.chat
            self.get_or_create_dog(chat._bot)
            text = msg.text.replace('—', '--')
            usr = msg.from_user
            Logger.debug(f"Telegram: {usr.username} >> {text}")
            user = self._server.get_or_create_user(str(usr.id), usr.username)
            message = Message(text, Mode.TELEGRAM)
            message.env_server(self._server)
            message.env_user(user)
            message.env_session(GDO_Session.for_user(user))
            if chat.type == ChatType.CHANNEL:
                channel = self._server.get_or_create_channel(str(chat.id), chat.title)
                message.env_channel(channel)
            asyncio.ensure_future(message.execute())
        except Exception as ex:
            Logger.exception(ex)
            await context.bot.send_message(chat_id=msg.chat.id, text=str(ex), parse_mode='HTML')

    async def gdo_send_to_channel(self, message: Message):
        channel = message._env_channel
        text = message._result
        Logger.debug(f"{channel.render_name()} >> {text}")
        try:
            await self._application.bot.send_message(chat_id=int(channel.get_name()), parse_mode='HTML', text=text)
        except Exception as ex:
            Logger.exception(ex)

    async def gdo_send_to_user(self, message: Message):
        text = message._result
        user = message._env_user
        Logger.debug(f"{user.render_name()} << {text}")
        try:
            await self._application.bot.send_message(chat_id=int(user.get_name()), parse_mode='HTML', text=text.strip())
        except Exception as ex:
            Logger.exception(ex)

    def get_or_create_dog(self, bot):
        from gdo.telegram.module_telegram import module_telegram
        mod = module_telegram.instance()
        user = self._server.get_or_create_user(str(bot.id), bot.username)
        mod.save_config_val('telegram_bot', user.get_id())
        return user

    def gdo_get_dog_user(self) -> GDO_User:
        from gdo.telegram.module_telegram import module_telegram
        return module_telegram.instance().cfg_bot()
