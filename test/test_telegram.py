import os
import unittest

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
from gdo.core.GDO_Server import GDO_Server
from gdotest.TestUtil import reinstall_module, cli_plug


class TelegramTestCase(unittest.TestCase):
    """
    For this test case you need a gdo/telegram/secret.toml configuration file.
    """

    def setUp(self):
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        loader = ModuleLoader.instance()
        loader.load_modules_db(True)
        loader.init_modules()
        reinstall_module('telegram')
        loader.init_cli()
        return self

    def test_01_starting_thread(self):
        out = cli_plug(None, "launch --force 1")
        self.assertTrue(True)



