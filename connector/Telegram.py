from gdo.core.Connector import Connector


class Telegram(Connector):
    _application: object

    def gdo_connect(self) -> bool:
        application = ApplicationBuilder().token('TOKEN').build()
