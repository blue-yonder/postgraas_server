import os
import uuid
import json
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import pytest

import postgraas_server.configuration as configuration
from postgraas_server.create_app import create_app
import postgraas_server.backends.postgres_cluster.postgres_cluster_driver as pgcd


CLUSTER_CONFIG = {
    "metadb":
    {
        "db_name": "postgraas",
        "db_username": "postgraas",
        "db_pwd": "postgraas12",
        "host": "localhost",
        "port": "54321"
    },
    "backend":
    {
        "type": "pg_cluster",
        "host": os.environ.get('PGHOST', 'localhost'),
        "port": os.environ.get('PGPORT', '5432'),
        "database": os.environ.get('PGDATABASE', 'postgres'),
        "username": os.environ.get('PGUSER', 'postgres'),
        "password": os.environ.get('PGPASSWORD', 'postgres'),
    }
}

CONFIGS = {
    'pg_cluster': CLUSTER_CONFIG,
}


def remove_digits(s):
    return ''.join(c for c in s if not c.isdigit())


def delete_test_database_and_user(db_name, username, config):
    try:
        pgcd.delete_database(db_name, config)
    except ValueError as e:
        pass
        # print(ValueError(e.args[0]))
    try:
        pgcd.delete_user(username, config)
    except ValueError as e:
        pass
        # print(ValueError(e.args[0]))


@pytest.fixture(params=['pg_cluster'])
def parametrized_setup(request, tmpdir):
    from postgraas_server.management_resources import db
    config = CONFIGS[request.param]
    this_app = create_app(config)
    this_app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
    this_app.use_reloader = False
    this_app.config['TESTING'] = True
    ctx = this_app.app_context()
    ctx.push()
    db.create_all()
    username, db_name = str(uuid.uuid4()).replace('-', '_'), str(uuid.uuid4()).replace('-', '_')
    request.cls.app_client = this_app.test_client()
    request.cls.db_name = remove_digits(db_name)
    request.cls.username = remove_digits(username)
    request.cls.backend = request.param
    yield
    if request.param == 'pg_cluster':
#        try:
            delete_test_database_and_user(db_name, username, config['backend'])
#        except Exception:
#            pass
    db.drop_all()
    ctx.pop()


class PostgraasApiTestBase:
    def get_postgraas_by_name(self, name, client):
        headers = {'Content-Type': 'application/json'}
        list = client.get('/api/v2/postgraas_instances', headers=headers)
        for instance in json.loads(list.data):
            if instance["postgraas_instance_name"] == name:
                return instance["id"]

    def delete_instance_by_name(self, db_credentials, client):
        id = self.get_postgraas_by_name(db_credentials["postgraas_instance_name"], client)
        db_pwd = db_credentials["db_pwd"]
        headers = {'Content-Type': 'application/json'}
        client.delete(
            '/api/v2/postgraas_instances/' + str(id),
            data=json.dumps({
                'db_pwd': db_pwd
            }),
            headers=headers
        )


@pytest.mark.usefixtures('parametrized_setup')
class TestPostgraasApi(PostgraasApiTestBase):

    def test_delete_db_and_user(self):
        backend_config = CONFIGS[self.backend]['backend']
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_postgres_cluster_delete",
            "db_name": 'test_delete_db_and_users',
            "db_username": 'test_delete_db_and_user',
            "db_pwd": 'test_db_pwd',
            "host": backend_config['host'],
            "port": backend_config['port']
        }
        delete_test_database_and_user(db_credentials['db_name'], db_credentials['db_username'], backend_config)
        exists = pgcd.check_db_or_user_exists(db_credentials['db_name'], db_credentials['db_username'], backend_config)
        assert exists is False
        pgcd.create_postgres_db(db_credentials, backend_config)
        exists = pgcd.check_db_or_user_exists(db_credentials['db_name'], db_credentials['db_username'], backend_config)
        assert exists is True
        response = self.app_client.post('/api/v2/postgraas_instances',
                                        data=json.dumps(db_credentials),
                                        headers={'Content-Type': 'application/json'})
        print(backend_config)
        print(response.get_data(as_text=True))
        assert ("database or user already exists" in json.loads(response.get_data(as_text=True))['description']) is True
        delete_test_database_and_user(db_credentials['db_name'], db_credentials['db_username'], backend_config)
        response = self.app_client.post('/api/v2/postgraas_instances',
                                        data=json.dumps(db_credentials),
                                        headers={'Content-Type': 'application/json'})
        print(response.get_data(as_text=True))
        assert ("test_delete_db_and_users" in json.loads(response.get_data(as_text=True))['db_name']) is True


    def test_create_postgres_instance_exists(self):
        backend_config = CONFIGS[self.backend]['backend']
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_create_postgres_instance_api",
            "db_name": 'test_create_postgres_instance_exists',
            "db_username": 'test_create_postgres_instance_exists_username',
            "db_pwd": 'test_db_pwd',
            "host": backend_config['host'],
            "port": backend_config['port']
        }
        delete_test_database_and_user(db_credentials['db_name'], db_credentials['db_username'], backend_config)
        exists = pgcd.check_db_or_user_exists(db_credentials['db_name'], db_credentials['db_username'], backend_config)
        assert exists is False
        print(db_credentials)
        pgcd.create_postgres_db(db_credentials, backend_config)
        exists = pgcd.check_db_or_user_exists(db_credentials['db_name'], db_credentials['db_username'], backend_config)
        assert exists is True
        response = self.app_client.post('/api/v2/postgraas_instances',
                                        data=json.dumps(db_credentials),
                                        headers={'Content-Type': 'application/json'})
        delete_test_database_and_user(db_credentials['db_name'], db_credentials['db_username'], backend_config)
        assert ("database or user already exists" in json.loads(response.get_data(as_text=True))['description']) is True

    def test_create_postgres_instance_username_exists(self):
        backend_config = CONFIGS[self.backend]['backend']
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_create_postgres_instance_api",
            "db_name": 'test_create_postgres_instance_exists',
            "db_username": 'test_create_postgres_instance_exists_username',
            "db_pwd": 'test_db_pwd',
            "host": backend_config['host'],
            "port": backend_config['port']
        }
        db_credentials_same_user = {
            "postgraas_instance_name": "tests_postgraas_test_create_postgres_instance_api",
            "db_name": 'test_create_postgres_instance_exists_new_db_name',
            "db_username": 'test_create_postgres_instance_exists_username',
            "db_pwd": 'test_db_pwd',
            "host": backend_config['host'],
            "port": backend_config['port']
        }
        delete_test_database_and_user(db_credentials['db_name'], db_credentials['db_username'], backend_config)
        exists = pgcd.check_db_or_user_exists(db_credentials['db_name'], db_credentials['db_username'], backend_config)
        assert exists is False
        print(db_credentials)
        pgcd.create_postgres_db(db_credentials, backend_config)
        exists = pgcd.check_db_or_user_exists(db_credentials['db_name'], db_credentials['db_username'], backend_config)
        assert exists is True
        with pytest.raises(ValueError):
            pgcd.create_postgres_db(db_credentials_same_user, backend_config)

        response = self.app_client.post('/api/v2/postgraas_instances',
                                        data=json.dumps(db_credentials_same_user),
                                        headers={'Content-Type': 'application/json'})
        delete_test_database_and_user(db_credentials['db_name'], db_credentials['db_username'], backend_config)
        delete_test_database_and_user(db_credentials_same_user['db_name'], db_credentials_same_user['db_username'],
                                      backend_config)
        assert ("database or user already exists" in json.loads(response.get_data(as_text=True))['description']) is True

    @pytest.mark.xfail(reason='Username now valid due to hardening against SQL injections.')
    def test_create_postgres_instance_bad_username(self):
        backend_config = CONFIGS[self.backend]['backend']
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_create_postgres_instance_api",
            "db_name": 'test_create_postgres_instance_exists',
            "db_username": 'test-invalid-username',
            "db_pwd": 'test_db_pwd',
            "host": backend_config['host'],
            "port": backend_config['port']
        }
        response = self.app_client.post('/api/v2/postgraas_instances',
                                        data=json.dumps(db_credentials),
                                        headers={'Content-Type': 'application/json'})
        print(response.get_data(as_text=True))
        delete_test_database_and_user(db_credentials['db_name'], db_credentials['db_username'], backend_config)
        assert ('syntax error at or near "-"' in json.loads(response.get_data(as_text=True))['msg']) is True
