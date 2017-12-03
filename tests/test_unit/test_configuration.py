import os
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import json

try:
    import secure_config.secrets
    HAS_SECURE_CONFIG=True
except ImportError:
    HAS_SECURE_CONFIG = False

import postgraas_server.configuration as cf
import pytest

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

    @pytest.mark.skipif(not HAS_SECURE_CONFIG,
                        reason="secure_config not installed")
    def test_secrets(self, tmpdir):
        expected_secret = secure_config.secrets.EncryptedSecret("v3rys3cur3", "correct_db_password")
        print(expected_secret)
        test_config = os.path.join(self.module_path, 'application_secure.cfg')
        secret_file = os.path.join(self.module_path, 'secret_file.json')
        config_undecrypted = cf.get_config(test_config)
        assert config_undecrypted['metadb']["db_password"] == expected_secret.dumps()
        config_decrypted = cf.get_config(test_config, secrets_file=secret_file)
        assert config_decrypted['metadb']["db_password"].decrypt() == "correct_db_password"
