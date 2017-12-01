import os
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import json

import postgraas_server.configuration as cf


class TestConfiguration:
    module_path = os.path.abspath(os.path.dirname(__file__))

    def test_default_config_filename(self):
        actual = cf.get_default_config_filename()
        expected = os.path.join(os.getcwd(), 'application.cfg')
        assert actual == expected

    def test_get_config(self):
        test_config = os.path.join(self.module_path, 'application.cfg')
        actual = cf.get_config(test_config)
        expected = 'postgraas'
        assert actual['metadb']['db_name'] == expected

    def test_get_user(self):
        config_string = '''
{
  "metadb":
    {
        "db_username": "postgraas_user"
    }
}
'''

        config = json.loads(config_string)
        username = cf.get_user(config)
        expected = 'postgraas_user'

        assert username == expected

        config_string = '''
{
  "metadb":
    {
        "server": "testserver1",
        "db_username": "postgraas_user"
    }
}
'''
        config = json.loads(config_string)
        username = cf.get_user(config)
        expected = 'postgraas_user@testserver1'

        assert username == expected

    def test_secrets(self, tmpdir):
        #TODO
        assert True
