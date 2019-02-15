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

    @pytest.mark.skipif(not HAS_SECURE_CONFIG,
                        reason="secure_config not installed")
    def test_get_meta_db_config_path(self, tmpdir):
        config_dict = {
                "metadb": {
                    "host": "thisserver.host",
                    "db_pwd": "$SECRET;0.1;AES256|613839656430373831386237333266306163376563343632663138346163323162333830333861666263326330663238346361666165313266373363316236370a613135396239326632663739376364313466616535333733626165333738303166303761366132633033346433376263393734643132336432393764623465330a65353264343035353236643533303464333561393637643966663165663739656130613435366564383065303834303066613338353631663430613061623833",
                    "port": "5432",
                    "db_name": "postgres",
                    "db_username": "postgraas_user",
                    "server": "thisserver"
               }
            }

        config = secure_config.secrets.load_secret_dict(password="v3rys3cur3", config_dict=config_dict)
        metadb_string = cf.get_meta_db_config_path(config)
        print(metadb_string)
        assert metadb_string == "postgresql://postgraas_user@thisserver:correct_db_password@thisserver.host:5432/postgres"

    @pytest.mark.skipif(not HAS_SECURE_CONFIG,
                        reason="secure_config not installed")
    def test_get_secure_password(self, tmpdir):
        config_dict = {
                "metadb": {
                    "db_pwd": "$SECRET;0.1;AES256|613839656430373831386237333266306163376563343632663138346163323162333830333861666263326330663238346361666165313266373363316236370a613135396239326632663739376364313466616535333733626165333738303166303761366132633033346433376263393734643132336432393764623465330a65353264343035353236643533303464333561393637643966663165663739656130613435366564383065303834303066613338353631663430613061623833",
               }
            }
        config = secure_config.secrets.load_secret_dict(password="v3rys3cur3", config_dict=config_dict)
        password_string = cf.get_password(config)
        print(password_string)
        assert password_string == "correct_db_password"

    def test_get_plain_password(self, tmpdir):
        config_dict = {
                "metadb": {
                    "db_pwd": "v3rys3cur3",
               }
            }
        password_string = cf.get_password(config_dict)
        print(password_string)
        assert password_string == "v3rys3cur3"
