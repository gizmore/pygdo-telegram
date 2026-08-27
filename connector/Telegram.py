import asyncio
from pathlib import Path
import time

from telegram._update import Update
from telegram.constants import ChatType, ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes

from gdo.base.Application import Application
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.base.Render import Mode
from gdo.base.Util import Strings, module_config_value
from gdo.core.Connector import Connector
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDO_User import GDO_User
from gdo.core.GDO_UserPermission import GDO_UserPermission
from gdo.core.GDT_UserType import GDT_UserType
from gdo.core.GDO_File import GDO_File
from gdo.telegram.connector.TelegramThread import TelegramThread

class Telegram(Connector):
    _application: any
    _thread: TelegramThread

    def render_user_connect_help(self) -> str:
        dog = module_config_value('telegram', 'telegram_user_name')
        return f'<a href="https://t.me/{dog}">t.me/{dog}</a>'

    def get_render_mode(self) -> Mode:
        return Mode.render_telegram

    def gdo_needs_authentication(self) -> bool:
        return False

    @staticmethod
    def is_channel_chat(chat_type: str) -> bool:
        return chat_type in (ChatType.CHANNEL, ChatType.SUPERGROUP, ChatType.GROUP)

    @staticmethod
    def text_or_none(text: str | None) -> str | None:
        return text.replace('—', '--') if text is not None else None

    @staticmethod
    def image_attachment(msg):
        """Return Telegram image metadata for a photo or image document."""
        if msg.photo:
            photo = msg.photo[-1]
            return photo.file_id, photo.file_unique_id, f'telegram-{photo.file_unique_id}.jpg', photo.file_size or 0
        document = msg.document
        if document and (document.mime_type or '').startswith('image/'):
            name = document.file_name or f'telegram-{document.file_unique_id}.image'
            return document.file_id, document.file_unique_id, name, document.file_size or 0
        return None

    async def store_image(self, attachment, context: ContextTypes.DEFAULT_TYPE) -> GDO_File:
        from gdo.telegram.module_telegram import module_telegram

        file_id, unique_id, filename, size = attachment
        if size > module_telegram.instance().cfg_image_max_bytes():
            raise ValueError('Telegram image exceeds the configured size limit.')
        directory = Path(Application.temp_path('telegram/images'))
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f'{time.time_ns()}-{unique_id}'
        remote = await context.bot.get_file(file_id)
        await remote.download_to_drive(custom_path=str(target))
        file = GDO_File.from_path(str(target), delete=True)
        file.set_val('file_name', filename)
        return file.insert()

    @staticmethod
    def image_notice(file: GDO_File, caption: str | None) -> str:
        prefix = caption.strip() + '\n' if caption else ''
        # IBDES is consumed locally by Mira.  Give that consumer an explicit
        # local-media link, rather than a Telegram API URL containing the bot
        # credential or a public download URL.  The file record remains useful
        # for ordinary PyGDO tooling, while file:// lets the receiver inspect
        # exactly this downloaded image.
        return f'{prefix}[Telegram image received: file://{file.get_path()} ({file.get_name()}, file #{file.get_id()})]'

    async def gdo_connect(self) -> bool:
        from gdo.telegram.module_telegram import module_telegram
        mod = module_telegram.instance()
        token = mod.cfg_api_key()
        Logger.debug('Connecting to Telegram.')
        self._application = ApplicationBuilder().token(token).build()
        handler = MessageHandler(None, self.handle_telegram_message)
        self._application.add_handler(handler)
        self._thread = TelegramThread(self)
        self._connected = True
        task = asyncio.create_task(self._thread.run(), name="Telegram")
        Application.TASKS.append(task)
        return True

    async def handle_telegram_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.edited_message or update.message
        if not msg:
            Logger.error("OOPS")
            return
        try:
            Application.tick()
            Application.mode(Mode.render_telegram)
            chat = msg.chat
            await self.get_or_create_dog(chat._bot)
            usr = msg.from_user
            user = await self._server.get_or_create_user(str(usr.id), usr.username)
            Application.set_current_user(user)
            attachment = self.image_attachment(msg)
            if attachment:
                file = await self.store_image(attachment, context)
                text = self.image_notice(file, self.text_or_none(msg.caption))
            else:
                text = self.text_or_none(msg.text)
            if text is None:
                return
            Logger.debug(f"Telegram: {usr.username} >> {text}")
            message = Message(text, Mode.render_telegram)
            message.env_server(self._server)
            message.env_user(user, True)
            if self.is_channel_chat(chat.type):
                channel = self._server.get_or_create_channel(str(chat.id), chat.title)
                message.env_channel(channel)
                await channel.on_user_joined(user)
            await message.execute()

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

    async def gdo_send_to_user(self, message: Message, notice: bool=False):
        text = message._result
        user = message._env_user
        Logger.debug(f"{user.render_name()} << {text}")
        await self.send_to_chat(user.get_name(), text, message._env_reply_to)

    async def send_to_chat(self, chat_id: str, text: str, reply_to: 'GDO_User'):
        lrt = 0 if reply_to is None else len(reply_to.render_name()) + 2
        chunks = Strings.split_boundary(text, 4096 - lrt)
        for chunk in chunks:
            if reply_to:
                chunk = f"{reply_to.render_name()}: {chunk}"
            await self._application.bot.send_message(chat_id=int(chat_id), parse_mode=ParseMode.HTML, text=chunk)

    async def send_image_to_chat(self, chat_id: str, file: GDO_File, caption: str = ''):
        if not file.is_image():
            raise ValueError('Only image files can be sent through Telegram.')
        with open(file.get_path(), 'rb') as handle:
            await self._application.bot.send_photo(chat_id=int(chat_id), photo=handle,
                                                   caption=caption or None, parse_mode=ParseMode.HTML)

    async def get_or_create_dog(self, bot) -> GDO_User:
        from gdo.telegram.module_telegram import module_telegram
        mod = module_telegram.instance()
        user = await self._server.get_or_create_user(str(bot.id), bot.username)
        user.save_val('user_type', GDT_UserType.CHAPPY)
        await GDO_UserPermission.grant(user, GDO_Permission.ADMIN)
        await GDO_UserPermission.grant(user, GDO_Permission.STAFF)
        await mod.save_config_val('telegram_bot', user.get_id())
        return user

    def gdo_get_dog_user(self) -> GDO_User:
        from gdo.telegram.module_telegram import module_telegram
        return module_telegram.instance().cfg_bot()
