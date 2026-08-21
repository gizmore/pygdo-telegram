from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDO_File import GDO_File
from gdo.core.GDT_Object import GDT_Object
from gdo.core.GDT_RestOfText import GDT_RestOfText
from gdo.telegram.connector.Telegram import Telegram


class image(Method):
    """Send an existing PyGDO image file to the current Telegram conversation."""

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'telegram.image'

    def gdo_user_permission(self) -> str | None:
        return 'staff'

    def gdo_connectors(self) -> str:
        return 'telegram'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Object('file').table(GDO_File.table()).not_null(),
            GDT_RestOfText('caption').max(1024),
        ]

    async def gdo_execute(self) -> GDT:
        file = self.param_value('file')
        if not file.is_image():
            return self.err('err_telegram_image_type')
        target = self._env_channel.get_name() if self._env_channel else self._message._env_reply_to.get_name()
        connector: Telegram = self._env_server.get_connector()
        await connector.send_image_to_chat(target, file, self.param_value('caption') or '')
        return self.msg('msg_telegram_image_sent', (file.get_name(),))
