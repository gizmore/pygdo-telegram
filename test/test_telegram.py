import asyncio
import os
import unittest

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
from gdo.base.Render import Render, Mode
from gdo.core.Connector import Connector
from gdo.core.GDO_Server import GDO_Server
from gdo.core.method.launch import launch
from gdo.telegram.connector.Telegram import Telegram
from gdotest.TestUtil import reinstall_module, text_plug


class TelegramTestCase(unittest.TestCase):
    """
    For this test case you need a gdo/telegram/secret.toml configuration file.
    """

    def setUp(self):
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        loader = ModuleLoader.instance()
        loader.load_modules_db(True)
        loader.init_modules(True, True)
        reinstall_module('telegram')
        loader.init_cli()

    def test_01_connector_registered(self):
        self.assertIn('telegram', Connector.AVAILABLE.keys(), "Connector was not added.")

    def test_02_render_telegram(self):
        out = text_plug(Mode.render_telegram, '$help')
        self.assertIn('Core', out, 'Telegram does not render help nicely.')
        self.assertNotIn('[0m', out, 'Telegram does render as CLI.')
        self.assertIn('<b>Core</b>', out, 'Telegram help must preserve HTML formatting.')

    def test_03_send_preserves_html(self):
        class Bot:
            sent = []

            async def send_message(self, **kwargs):
                self.sent.append(kwargs)

        class TelegramApplication:
            bot = Bot()

        connector = Telegram()
        connector._application = TelegramApplication()
        asyncio.run(connector.send_to_chat('123', '<b>Core</b>', None))
        self.assertEqual('<b>Core</b>', connector._application.bot.sent[0]['text'])
        self.assertEqual('HTML', connector._application.bot.sent[0]['parse_mode'])

    def test_04_group_messages_create_channels(self):
        self.assertTrue(Telegram.is_channel_chat('group'))
        self.assertTrue(Telegram.is_channel_chat('supergroup'))
        self.assertTrue(Telegram.is_channel_chat('channel'))
        self.assertFalse(Telegram.is_channel_chat('private'))

    def test_05_non_text_messages_are_ignored(self):
        self.assertIsNone(Telegram.text_or_none(None))
        self.assertEqual('a--b', Telegram.text_or_none('a—b'))

    def test_06_channel_creation(self):
        server = GDO_Server.get_by_connector('Telegram')
        channel1 = server.get_or_create_channel(str(-4139465915), 'WeChall')
        channel2 = server.get_or_create_channel(str(-4139465915), 'WeChall')
        self.assertEqual(channel1, channel2, 'Channel cannot be gotten from memory.')
