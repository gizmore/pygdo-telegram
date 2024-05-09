import tomlkit

from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.core.Connector import Connector
from gdo.core.GDO_Server import GDO_Server
from gdo.core.GDT_Name import GDT_Name
from gdo.core.GDT_Secret import GDT_Secret
from gdo.telegram.connector.Telegram import Telegram


class module_telegram(GDO_Module):

    def gdo_module_config(self) -> list[GDT]:
        bot_name = ''
        username = ''
        apikey = ''
        try:
            path = self.file_path('secret.toml')
            with open(path, 'r') as file:
                toml = tomlkit.load(file)
                bot_name = toml['bot_name']
                username = toml['bot_user']
                apikey = toml['api_key']
        except FileNotFoundError:
            pass
        return [
            GDT_Name('telegram_bot_name').initial(bot_name),
            GDT_Secret('telegram_user_name').initial(username),
            GDT_Secret('telegram_api_key').initial(apikey),
        ]

    def cfg_bot_displayname(self):
        return self.get_config_val('telegram_bot_name')

    def cfg_bot_user_name(self):
        return self.get_config_val('telegram_user_name')

    def cfg_api_key(self) -> str:
        return self.get_config_val('telegram_api_key')

    def gdo_init(self):
        Connector.register(Telegram, True)

    def gdo_install(self):
        if not GDO_Server.get_by_connector('Telegram'):
            GDO_Server.blank({
                'serv_name': 'Telegram',
                'serv_username': self.cfg_bot_user_name(),
                'serv_connector': 'Telegram',
            }).insert()


