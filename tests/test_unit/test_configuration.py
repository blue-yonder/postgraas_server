import unittest
import os
import ConfigParser

import postgraas_server.configuration as cf


class TestConfiguration(unittest.TestCase):
    module_path = os.path.abspath(os.path.dirname(__file__))

    def test_default_config_filename(self):
        actual = cf.get_default_config_filename()
        expected = os.path.join(os.getcwd(), 'postgraas_server.cfg')
        self.assertEqual(actual, expected)

    def test_get_config(self):
        test_config = os.path.join(self.module_path, 'postgraas_server.cfg')
        actual = cf.get_config(test_config)
        expected = 'postgraas'
        self.assertEqual(actual.get('metadb', 'db_name'), expected)


