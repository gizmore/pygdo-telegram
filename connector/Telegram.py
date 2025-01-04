import asyncio

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes
from telegram.ext import Application as TelegramApp

from gdo.base.Application import Application
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.base.Render import Mode
from gdo.base.Util import Strings, html
from gdo.core.Connector import Connector
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDO_Session import GDO_Session
from gdo.core.GDO_User import GDO_User
from gdo.core.GDO_UserPermission import GDO_UserPermission
from gdo.core.GDT_UserType import GDT_UserType
from gdo.telegram.connector.TelegramThread import TelegramThread

class Telegram(Connector):
    _application: TelegramApp
    _thread: TelegramThread

    def get_render_mode(self) -> Mode:
        return Mode.TELEGRAM

    def gdo_needs_authentication(self) -> bool:
        return False

    def gdo_connect(self) -> bool:
        from gdo.telegram.module_telegram import module_telegram
        mod = module_telegram.instance()
        token = mod.cfg_api_key()
        Logger.debug(f'Connecting to telegram with token {token}')
        self._application = ApplicationBuilder().token(token).build()
        handler = MessageHandler(None, self.handle_telegram_message)
        self._application.add_handler(handler)
        self._thread = TelegramThread(self)
        asyncio.run(self._thread.run())
        self._connected = True
        return True

    async def handle_telegram_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.edited_message or update.message
        if not msg:
            Logger.error("OOPS")
            return
        try:
            Application.tick()
            chat = msg.chat
            self.get_or_create_dog(chat._bot)
            text = msg.text.replace('—', '--')
            usr = msg.from_user
            Logger.debug(f"Telegram: {usr.username} >> {text}")
            user = self._server.get_or_create_user(str(usr.id), usr.username)
            message = Message(text, Mode.TELEGRAM)
            message.env_server(self._server)
            message.env_user(user, True)
            if chat.type in (ChatType.CHANNEL, ChatType.SUPERGROUP, ChatType.GROUP) :
                channel = self._server.get_or_create_channel(str(chat.id), chat.title)
                message.env_channel(channel)
                channel.on_user_joined(user)
            asyncio.ensure_future(message.execute())

        except Exception as ex:
            Logger.exception(ex)
            await context.bot.send_message(chat_id=msg.chat.id, text=str(ex), parse_mode='HTML')

    async def gdo_send_to_channel(self, message: Message):
        text = message._result
        channel = message._env_channel
        Logger.debug(f"{channel.render_name()} << {text}")
        # prefix = f'{message._env_user.render_name()}: ' if not message._thread_user else ''
        # text = f"{prefix}{text}"
        await self.send_to_chat(channel.get_name(), text, message._env_reply_to)

    async def gdo_send_to_user(self, message: Message):
        text = message._result
        user = message._env_user
        Logger.debug(f"{user.render_name()} << {text}")
        await self.send_to_chat(user.get_name(), text, message._env_reply_to)

    async def send_to_chat(self, chat_id: str, text: str, reply_to: str):
        lrt = 0 if reply_to is None else len(reply_to) + 2
        chunks = Strings.split_boundary(html(text), 4096 - lrt)
        for chunk in chunks:
            if reply_to:
                chunk = f"{reply_to}: {chunk}"
            await self._application.bot.send_message(chat_id=int(chat_id), parse_mode='HTML', text=chunk)

    def get_or_create_dog(self, bot) -> GDO_User:
        from gdo.telegram.module_telegram import module_telegram
        mod = module_telegram.instance()
        user = self._server.get_or_create_user(str(bot.id), bot.username)
        user.save_val('user_type', GDT_UserType.CHAPPY)
        GDO_UserPermission.grant(user, GDO_Permission.ADMIN)
        GDO_UserPermission.grant(user, GDO_Permission.STAFF)
        mod.save_config_val('telegram_bot', user.get_id())
        return user

    def gdo_get_dog_user(self) -> GDO_User:
        from gdo.telegram.module_telegram import module_telegram
        return module_telegram.instance().cfg_bot()
