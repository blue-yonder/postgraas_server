import os
import ConfigParser
import StringIO
from cryptography.fernet import Fernet

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
        assert actual.get('metadb', 'db_name') == expected

    def test_get_user(self):
        config_string = '''
[metadb]
db_username = postgraas_user
'''

        config = ConfigParser.ConfigParser()

        config.readfp(StringIO.StringIO(config_string))
        username = cf.get_user(config)
        expected = 'postgraas_user'

        assert username == expected

        config_string = '''
[metadb]
server = testserver1
db_username = postgraas_user
'''
        config = ConfigParser.ConfigParser()

        config.readfp(StringIO.StringIO(config_string))
        username = cf.get_user(config)
        expected = 'postgraas_user@testserver1'

        assert username == expected

    def test_secrets(self, tmpdir):
        secrets_file = tmpdir.join('secrets')
        key = Fernet.generate_key()
        print(key)
        f = Fernet(key)
        secrets_file.write('{{"encryption_key": "{}"}}'.format(key))
        test_config = os.path.join(self.module_path, 'application.cfg')
        cfg_file = tmpdir.join('application.cfg')
        cfg_file.write(f.encrypt(open(test_config, 'rb').read()))
        config = cf.get_config(cfg_file.strpath, secrets_file=secrets_file.strpath)
        assert config.get('metadb', 'db_name') == 'postgraas'
