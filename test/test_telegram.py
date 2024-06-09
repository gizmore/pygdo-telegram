import os
import unittest

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
from gdo.base.Render import Render, Mode
from gdo.core.Connector import Connector
from gdo.core.method.launch import launch
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
        out = text_plug(Mode.TELEGRAM, '$help')
        self.assertIn('Core', out, 'Telegram does not render help nicely.')
        self.assertNotIn('[0m', out, 'Telegram does render as CLI.')
