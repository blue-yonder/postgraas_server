import uuid
import json
import os
import pytest

import postgraas_server.backends.docker.postgres_instance_driver as pid
import postgraas_server.backends.postgres_cluster.postgres_cluster_driver as pgcd
import postgraas_server.configuration as configuration
from postgraas_server.backends.exceptions import PostgraasApiException
from postgraas_server.create_app import create_app
from postgraas_server.management_resources import DBInstance

DOCKER_CONFIG = {
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
        "type": "docker"
    }
}

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


def delete_all_test_database_and_user(config):
    con = pgcd._create_pg_connection(config)
    cur = con.cursor()
    cur.execute(
        '''SELECT d.datname, u.usename
           FROM pg_database d
           JOIN pg_user u ON (d.datdba = u.usesysid);''')
    for db in cur:
        if db[0].startswith("tests_postgraas_"):
            delete_test_database_and_user(db[0], db[1], config)
    cur.execute(
        '''SELECT u.usename
           FROM pg_user u;''')
    for db in cur:
        if db[0].startswith("tests_postgraas_"):
            pgcd.delete_user(db[0], config)


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
    request.cls.this_app = this_app
    request.cls.app_client = this_app.test_client()
    request.cls.db_name = remove_digits(db_name)
    request.cls.username = remove_digits(username)
    request.cls.backend = request.param
    try:
        yield
    except Exception:
        pass
    if request.param == 'docker':
        delete_all_test_postgraas_container()
    elif request.param == 'pg_cluster':
        delete_all_test_database_and_user(config['backend'])
    db.drop_all()
    ctx.pop()


@pytest.mark.usefixtures('parametrized_setup')
class TestPostgraasApi():
    def test_create_and_delete_postgres_instance(self):
        db_credentials = {
            "db_name": 'tests_postgraas_instance_name',
            "db_username": 'tests_postgraas_db_username',
            "db_pwd": 'test_db_pwd',
            "host": pid.get_hostname(),
            "port": pid.get_open_port()
        }
        db_entry = DBInstance(
            postgraas_instance_name=db_credentials['db_name'],
            db_name=db_credentials['db_name'],
            username=db_credentials['db_username'],
            password="",
            hostname=db_credentials['host'],
            port=db_credentials['port']
        )
        db_entry.container_id = self.this_app.postgraas_backend.create(db_entry, db_credentials)
        self.this_app.postgraas_backend.delete(db_entry)
        assert True

    def test_create_postgraas_twice(self):
        db_credentials = {
            "db_name": 'tests_postgraas_instance_name',
            "db_username": 'tests_postgraas_db_username',
            "db_pwd": 'test_db_pwd',
            "host": pid.get_hostname(),
            "port": pid.get_open_port()
        }
        db_entry = DBInstance(
            postgraas_instance_name=db_credentials['db_name'],
            db_name=db_credentials['db_name'],
            username=db_credentials['db_username'],
            password="",
            hostname=db_credentials['host'],
            port=db_credentials['port']
        )
        db_entry.container_id = self.this_app.postgraas_backend.create(db_entry, db_credentials)
        with pytest.raises(PostgraasApiException) as excinfo:
            db_entry.container_id = self.this_app.postgraas_backend.create(db_entry, db_credentials)
        if self.backend == "pg_cluster":
            assert excinfo.value.message == 'db or user already exists'
        elif self.backend == "docker":
            assert excinfo.value.message == 'Container exists already'
        self.this_app.postgraas_backend.delete(db_entry)
        assert True

    @pytest.mark.xfail(reason='Username now valid due to hardening against SQL injections.')
    def test_create_postgraas_bad_username(self):
        db_credentials = {
            "db_name": 'tests_postgraas_instance_name',
            "db_username": 'tests_postgraas_db-bad username',
            "db_pwd": 'test_db_pwd',
            "host": pid.get_hostname(),
            "port": pid.get_open_port()
        }
        db_entry = DBInstance(
            postgraas_instance_name=db_credentials['db_name'],
            db_name=db_credentials['db_name'],
            username=db_credentials['db_username'],
            password="",
            hostname=db_credentials['host'],
            port=db_credentials['port']
        )
        if self.backend == "pg_cluster":
            with pytest.raises(PostgraasApiException) as excinfo:
                db_entry.container_id = self.this_app.postgraas_backend.create(db_entry, db_credentials)
                self.this_app.postgraas_backend.delete(db_entry)
            assert 'syntax error at or near "-"' in excinfo.value.message

    def test_delete_nonexisting_db(self):
        db_credentials = {
            "db_name": 'tests_postgraas_instance_name',
            "db_username": 'tests_postgraas_db-bad username',
            "db_pwd": 'test_db_pwd',
            "host": pid.get_hostname(),
            "port": pid.get_open_port()
        }
        db_entry = DBInstance(
            postgraas_instance_name=db_credentials['db_name'],
            db_name=db_credentials['db_name'],
            username=db_credentials['db_username'],
            password="",
            hostname=db_credentials['host'],
            port=db_credentials['port'],
            container_id="4n8nz48az49prdmdmprmr4doesnotexit"

        )
        with pytest.raises(PostgraasApiException) as excinfo:
            db_entry.container_id = self.this_app.postgraas_backend.delete(db_entry)
        assert 'does not exist' in excinfo.value.message
