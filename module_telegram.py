import tomlkit

from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.core.GDT_Name import GDT_Name
from gdo.core.GDT_Secret import GDT_Secret


class module_telegram(GDO_Module):

    def gdo_module_config(self) -> list[GDT]:
        bot_name = ''
        username = ''
        apikey = ''
        try:
            path = self.file_path('secret.toml')
            toml = tomlkit.load(path)
            bot_name = toml['']
            username = toml['']
            apikey = toml['']
        except FileNotFoundError:
            pass
        return [
            GDT_Name('telegram_bot_name').initial(bot_name),
            GDT_Secret('telegram_user_name').initial(username),
            GDT_Secret('telegram_api_key').initial(apikey),
        ]
