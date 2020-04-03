import json
import os
import uuid

import docker
import pytest
import psycopg2
from mock import patch, MagicMock, Mock
from contextlib import closing

import postgraas_server.backends.docker.postgres_instance_driver as pid
import postgraas_server.backends.postgres_cluster.postgres_cluster_driver as pgcd
import postgraas_server.configuration as configuration
from postgraas_server.backends.exceptions import PostgraasApiException
from postgraas_server.create_app import create_app
from .utils import wait_for_postgres_listening

DOCKER_CONFIG = {
    "metadb": {
        "db_name": "postgraas",
        "db_username": "postgraas",
        "db_pwd": "postgraas12",
        "host": "localhost",
        "port": "54321"
    },
    "backend": {
        "type": "docker"
    }
}

CLUSTER_CONFIG = {
    "metadb": {
        "db_name": "postgraas",
        "db_username": "postgraas",
        "db_pwd": "postgraas12",
        "host": "localhost",
        "port": "54321"
    },
    "backend": {
        "type": "pg_cluster",
        "host": os.environ.get('PGHOST', 'localhost'),
        "port": os.environ.get('PGPORT', '5432'),
        "database": os.environ.get('PGDATABASE', 'postgres'),
        "username": os.environ.get('PGUSER', 'postgres'),
        "password": os.environ.get('PGPASSWORD', 'postgres'),
    }
}

CONFIGS = {
    'docker': DOCKER_CONFIG,
    'pg_cluster': CLUSTER_CONFIG,
}


def remove_digits(s):
    return ''.join(c for c in s if not c.isdigit())


def delete_all_test_postgraas_container():
    c = pid._docker_client()
    for container in c.containers.list():
        if container.name.startswith("tests_postgraas_"):
            container.remove(force=True)


def delete_test_database_and_user(db_name, username, config):
    pgcd.delete_database(db_name, config)
    pgcd.delete_user(username, config)


@pytest.fixture(params=['docker', 'pg_cluster'])
def parametrized_setup(request, tmpdir):
    from postgraas_server.management_resources import db
    cfg = tmpdir.join('config')
    with open(cfg.strpath, "w") as fp:
        json.dump(CONFIGS[request.param], fp)

    config = configuration.get_config(cfg.strpath)
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
    if request.param == 'docker':
        delete_all_test_postgraas_container()
    elif request.param == 'pg_cluster':
        try:
            delete_test_database_and_user(db_name, username, dict(config.items('backend')))
        except Exception:
            pass
    db.drop_all()
    ctx.pop()


@pytest.fixture()
def docker_setup(request, tmpdir):
    from postgraas_server.management_resources import db
    cfg = tmpdir.join('config')
    with open(cfg.strpath, "w") as fp:
        json.dump(CONFIGS['docker'], fp)

    this_app = create_app(configuration.get_config(cfg.strpath))
    this_app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
    this_app.use_reloader = False
    this_app.config['TESTING'] = True
    ctx = this_app.app_context()
    ctx.push()
    db.create_all()
    request.cls.app_client = this_app.test_client()
    yield
    delete_all_test_postgraas_container()
    db.drop_all()
    ctx.pop()


class PostgraasApiTestBase(object):
    def get_postgraas_by_name(self, name, client):
        headers = {'Content-Type': 'application/json'}
        instances = client.get('/api/v2/postgraas_instances', headers=headers)
        for instance in json.loads(instances.get_data(as_text=True)):
            if instance["postgraas_instance_name"] == name:
                return instance["id"]
        return None

    def delete_instance_by_name(self, db_credentials, client):
        instance_id = self.get_postgraas_by_name(db_credentials["postgraas_instance_name"], client)
        if instance_id is not None:
            db_pwd = db_credentials["db_pwd"]
            headers = {'Content-Type': 'application/json'}
            client.delete(
                '/api/v2/postgraas_instances/' + str(instance_id),
                data=json.dumps({
                    'db_pwd': db_pwd
                }),
                headers=headers
            )


@pytest.mark.usefixtures('docker_setup')
class TestPostgraasApiDocker(PostgraasApiTestBase):
    def test_create_postgres_instance_api(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_create_postgres_instance_api",
            "db_name": "test_create_postgres_instance",
            "db_username": "db_user",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials, self.app_client)
        headers = {'Content-Type': 'application/json'}
        result = self.app_client.post(
            '/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials)
        )
        created_db = json.loads(result.get_data(as_text=True))
        assert created_db["db_name"] == 'test_create_postgres_instance'
        self.delete_instance_by_name(db_credentials, self.app_client)

    def test_create_postgres_instance_api_with_fully_qualified_user(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_create_postgres_instance_api",
            "db_name": "test_create_postgres_instance",
            "db_username": "db_user@tests_postgraas_test_create_postgres_instance_api",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials, self.app_client)
        headers = {'Content-Type': 'application/json'}
        result = self.app_client.post(
            '/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials)
        )
        created_db = json.loads(result.get_data(as_text=True))
        assert created_db["db_name"] == 'test_create_postgres_instance'
        self.delete_instance_by_name(db_credentials, self.app_client)

    def test_create_postgres_instance_api_with_postgres_as_user(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_create_postgres_instance_api",
            "db_name": "test_create_postgres_instance",
            "db_username": "postgres",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials, self.app_client)
        headers = {'Content-Type': 'application/json'}
        result = self.app_client.post(
            '/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials)
        )
        assert result.status_code == 422
        self.delete_instance_by_name(db_credentials, self.app_client)

    def test_create_postgres_instance_api_with_postgres_at_example_com_as_user(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_create_postgres_instance_api",
            "db_name": "test_create_postgres_instance",
            "db_username": "postgres@example.com",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials, self.app_client)
        headers = {'Content-Type': 'application/json'}
        result = self.app_client.post(
            '/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials)
        )
        assert result.status_code == 422
        self.delete_instance_by_name(db_credentials, self.app_client)

    def test_create_postgres_instance_api_with_postgres_at_localhost_as_user(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_create_postgres_instance_api",
            "db_name": "test_create_postgres_instance",
            "db_username": "postgres@localhost",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials, self.app_client)
        headers = {'Content-Type': 'application/json'}
        result = self.app_client.post(
            '/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials)
        )
        assert result.status_code == 422
        self.delete_instance_by_name(db_credentials, self.app_client)

    def test_create_docker_fails(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_create_postgres_instance_api",
            "db_name": "test_create_postgres_instance",
            "db_username": "db_user",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials, self.app_client)
        headers = {'Content-Type': 'application/json'}

        def raise_apierror(*args, **kwargs):
            raise PostgraasApiException('let create fail')

        with patch.object(docker.models.containers.ContainerCollection, 'create', raise_apierror):
            result = self.app_client.post(
                '/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials)
            )
        created_db = json.loads(result.get_data(as_text=True))
        assert 'let create fail' in created_db[
            "msg"
        ], 'unexpected error message for docker create failure'

    def test_delete_docker_notfound(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_delete_docker_notfound",
            "db_name": "test_create_postgres_instance",
            "db_username": "db_user",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials, self.app_client)
        headers = {'Content-Type': 'application/json'}
        result = self.app_client.post(
            '/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials)
        )
        created_db = json.loads(result.get_data(as_text=True))
        wait_success = wait_for_postgres_listening(created_db['container_id'])
        assert wait_success is True, 'postgres did not come up within 10s (or unexpected docker image log output)'

        def raise_not_found(*args, **kwargs):
            raise docker.errors.NotFound('raise for testing from mock')

        with patch.object(docker.models.containers.ContainerCollection, 'get', raise_not_found):
            res = self.app_client.delete(
                '/api/v2/postgraas_instances/' + str(created_db["postgraas_instance_id"]),
                data=json.dumps({
                    'db_pwd': db_credentials['db_pwd']
                }),
                headers=headers
            )
            res = json.loads(res.get_data(as_text=True))
        assert res['status'] == 'success'
        assert 'deleted postgraas instance, but container was not found' in res['msg']

    def test_driver_name_exists(self):
        db_credentials = {
            "db_name": 'test_db_name',
            "db_username": 'test_db_username',
            "db_pwd": 'test_db_pwd',
            "host": pid.get_hostname(),
            "port": pid.get_open_port()
        }
        if pid.check_container_exists('test_instance_name'):
            pid.delete_postgres_instance('test_instance_name')
        id0 = pid.create_postgres_instance('test_instance_name', db_credentials)
        with pytest.raises(ValueError):
            pid.create_postgres_instance('test_instance_name', db_credentials)

        pid.delete_postgres_instance(id0)
        assert pid.check_container_exists(id0) is False, "container exists after it was deleted"


@pytest.mark.usefixtures('parametrized_setup')
class TestPostgraasApi(PostgraasApiTestBase):
    def test_create_postgres_instance(self):
        db_credentials = {
            "db_name": 'test_db_name',
            "db_username": 'test_db_username',
            "db_pwd": 'test_db_pwd',
            "host": pid.get_hostname(),
            "port": pid.get_open_port()
        }
        mock_c = MagicMock()
        mock_c.id = 'EW3uvF3C3tLce9Eo5D76NbQe'
        mock_create = Mock(return_value=mock_c)
        with patch.object(docker.models.containers.ContainerCollection, 'create', mock_create):
            result = pid.create_postgres_instance(
                'tests_postgraas_test_instance_name', db_credentials
            )
        assert result == 'EW3uvF3C3tLce9Eo5D76NbQe'

    def test_create_postgres_instance_with_fully_qualified_username(self):
        db_credentials = {
            "db_name": 'test_db_name',
            "db_username": 'test_db_username@{}'.format(pid.get_hostname()),
            "db_pwd": 'test_db_pwd',
            "host": pid.get_hostname(),
            "port": pid.get_open_port()
        }
        mock_c = MagicMock()
        mock_c.id = 'dN4IsDN5eOqeCgli23MlxeTA'
        mock_create = Mock(return_value=mock_c)
        with patch.object(docker.models.containers.ContainerCollection, 'create', mock_create):
            result = pid.create_postgres_instance(
                'tests_postgraas_test_instance_name', db_credentials
            )
        assert result == 'dN4IsDN5eOqeCgli23MlxeTA'

    def test_delete_postgres_instance_api(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_delete_postgres_instance_api",
            "db_name": self.db_name,
            "db_username": self.username,
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials, self.app_client)
        headers = {'Content-Type': 'application/json'}
        result = self.app_client.post(
            '/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials)
        )
        created_db = json.loads(result.get_data(as_text=True))

        if self.backend == 'docker':
            wait_success = wait_for_postgres_listening(created_db['container_id'])
            assert wait_success is True, 'postgres did not come up within 10s (or unexpected docker image log output)'

        delete_result = self.app_client.delete(
            '/api/v2/postgraas_instances/' + str(created_db["postgraas_instance_id"]),
            data=json.dumps({
                'db_pwd': 'wrong_password'
            }),
            headers=headers
        )
        deleted_db = json.loads(delete_result.get_data(as_text=True))
        assert delete_result.status_code == 401
        assert deleted_db["status"] == 'failed'
        assert 'password authentication failed' in deleted_db[
            'msg'
        ], 'unexpected message for wrong password'

        def raise_apierror(*args, **kwargs):
            raise PostgraasApiException('let remove fail')

        with patch.object(docker.models.containers.Container, 'remove', raise_apierror):
            with patch.object(pgcd, 'delete_database', raise_apierror):
                delete_result = self.app_client.delete(
                    '/api/v2/postgraas_instances/' + str(created_db["postgraas_instance_id"]),
                    data=json.dumps({
                        'db_pwd': db_credentials['db_pwd']
                    }),
                    headers=headers
                )
                deleted_db = json.loads(delete_result.get_data(as_text=True))
                assert deleted_db["status"] == 'failed'
                assert 'let remove fail' in deleted_db[
                    'msg'
                ], 'unexpected error message on docker rm failure'

        delete_result = self.app_client.delete(
            '/api/v2/postgraas_instances/' + str(created_db["postgraas_instance_id"]),
            data=json.dumps({
                'db_pwd': db_credentials['db_pwd']
            }),
            headers=headers
        )
        deleted_db = json.loads(delete_result.get_data(as_text=True))
        assert deleted_db["status"] == 'success'

    def test_delete_notfound(self):
        headers = {'Content-Type': 'application/json'}
        res = self.app_client.delete(
            '/api/v2/postgraas_instances/123456789',
            data=json.dumps({
                'db_pwd': '123'
            }),
            headers=headers
        )
        assert res.status_code == 404
        res = json.loads(res.get_data(as_text=True))
        assert res['status'] == 'failed'
        assert "123456789" in res['msg'], 'unexpected error message'

    def test_delete_postgres_instance_api_with_active_sessions(self):
        db_credentials = {
            "postgraas_instance_name": "test_active_sessions_instance",
            "db_name": "test_active_sessions_db",
            "db_username": "test_active_sessions_user",
            "db_pwd": "secret"
        }
        headers = {'Content-Type': 'application/json'}
        result = self.app_client.post(
            '/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials)
        )
        created_db = json.loads(result.get_data(as_text=True))

        if self.backend == 'docker':
            wait_success = wait_for_postgres_listening(created_db['container_id'])
            assert wait_success is True, 'postgres did not come up within 10s (or unexpected docker image log output)'

        try:
            with closing(psycopg2.connect(
                    user=db_credentials["db_username"],
                    password=db_credentials["db_pwd"],
                    host=os.environ.get('PGHOST', 'localhost'),
                    port=created_db["port"],
                    dbname=db_credentials["db_name"]
            )):
                delete_result = self.app_client.delete(
                    '/api/v2/postgraas_instances/' + str(created_db["postgraas_instance_id"]),
                    data=json.dumps({
                        'db_pwd': db_credentials['db_pwd']
                    }),
                    headers=headers
                )
                deleted_db = json.loads(delete_result.get_data(as_text=True))
                assert delete_result.status_code == 409
                assert deleted_db["status"] == 'failed'
                assert 'active sessions' in deleted_db[
                    'msg'
                ], 'unexpected message for active sessions in the database'
        except Exception:
            pass

        delete_result = self.app_client.delete(
            '/api/v2/postgraas_instances/' + str(created_db["postgraas_instance_id"]),
            data=json.dumps({
                'db_pwd': db_credentials['db_pwd']
            }),
            headers=headers
        )

        deleted_db = json.loads(delete_result.get_data(as_text=True))
        assert delete_result.status_code == 200
        assert deleted_db["status"] == 'success'

    def test_create_postgres_instance_name_exists(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_my_postgraas_twice",
            "db_name": self.db_name,
            "db_username": self.username,
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials, self.app_client)
        headers = {'Content-Type': 'application/json'}
        self.app_client.post(
            '/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials)
        )
        second = self.app_client.post(
            '/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials)
        )
        assert second.status_code == 409  # Conflict
        assert second.get_data(as_text=True) == json.dumps(
            {
                "msg": "postgraas_instance_name already exists tests_postgraas_my_postgraas_twice"
            }
        ) + "\n"

        self.delete_instance_by_name(db_credentials, self.app_client)

    def test_return_postgres_instance_api(self):
        db_credentials = {
            u"postgraas_instance_name": u"tests_postgraas_test_return_postgres_instance_api",
            u"db_name": self.db_name,
            u"db_username": self.username,
            u"db_pwd": u"secret"
        }
        self.delete_instance_by_name(db_credentials, self.app_client)
        headers = {'Content-Type': 'application/json'}
        result = self.app_client.post(
            '/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials)
        )
        created_db = json.loads(result.get_data(as_text=True))
        created_db_id = created_db['postgraas_instance_id']
        actual = self.app_client.get(
            'api/v2/postgraas_instances/{}'.format(created_db_id), headers=headers
        )
        assert actual.status_code == 200
        actual_data = json.loads(actual.get_data(as_text=True))
        actual_data.pop('container_id')
        actual_data.pop('port')
        actual_data.pop('creation_timestamp')
        expected = {
            u'postgraas_instance_name': u'tests_postgraas_test_return_postgres_instance_api',
            u'db_name': self.db_name,
            u'username': self.username,
            u'password': u'',
            u'hostname': self.app_client.application.postgraas_backend.hostname,
            u'id': created_db_id,
        }
        assert actual_data == expected

        self.delete_instance_by_name(db_credentials, self.app_client)

    def test_empty_password(self):
        instance_name = "test_empty_password"
        db_credentials = {
            "postgraas_instance_name": instance_name,
            "db_name": self.db_name,
            "db_username": self.username,
            "db_pwd": "",
        }
        self.delete_instance_by_name(db_credentials, self.app_client)
        headers = {'Content-Type': 'application/json'}
        result = self.app_client.post(
            '/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials)
        )
        created_db = json.loads(result.get_data(as_text=True))

        assert result.status_code == 400
        print(created_db)
        assert 'password may not be empty' in created_db["msg"]
