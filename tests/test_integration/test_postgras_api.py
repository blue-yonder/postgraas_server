import unittest
import os
from mock import patch
import json
import postgraas_server.configuration as configuration
from postgraas_server.create_app import create_app
import postgraas_server.postgres_instance_driver as pid
import docker
from docker.errors import APIError


class TestPostgraasApi(unittest.TestCase):

    def get_postgraas_by_name(self, name):
        headers = {'Content-Type': 'application/json'}
        list = self.app.get('/api/v2/postgraas_instances', headers=headers)
        for instance in json.loads(list.data):
            if instance["postgraas_instance_name"] == name:
                return instance["id"]

    def delete_instance_by_name(self, db_credentials):
        id = self.get_postgraas_by_name(db_credentials["postgraas_instance_name"])
        self.app.delete('/api/v2/postgraas_instances/' + str(id))

    def delete_all_test_postgraas_container(self):
        c = docker.Client(base_url='unix://var/run/docker.sock',
                            timeout=30,
                            version='auto')
        containers = c.containers()
        for container in containers:
            for name in container['Names']:
                if name.startswith("/tests_postgraas_") and "postgraas" in container['Labels']:
                    c.remove_container(container['Id'], force=True)

    def setUp(self):
        self.module_path = os.path.abspath(os.path.dirname(__file__))
        self.this_app = create_app(configuration.get_config(os.path.join(self.module_path, 'postgraas_server.cfg')))
        #self.this_app.debug = True
        self.this_app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        self.this_app.use_reloader = False
        self.this_app.config['TESTING'] = True
        self.app = self.this_app.test_client()
        self.delete_all_test_postgraas_container()
        from postgraas_server.management_resources import db
        with self.this_app.app_context():
            db.drop_all()
            db.create_all()

    def tearDown(self):
        self.delete_all_test_postgraas_container()
        from postgraas_server.management_resources import db
        with self.this_app.app_context():
            db.drop_all()

    @patch.object(docker.Client, 'create_container', return_value={'Id': 'fy8rfsufusgsufbvluluivhhvsbr'})
    @patch.object(docker.Client, 'start', return_value=None)
    def test_create_postgres_instance(self, mockerclientstart, mockerclientcreate):
        db_credentials = {
            "db_name": 'test_db_name',
            "db_username": 'test_db_username',
            "db_pwd": 'test_db_pwd',
            "host": pid.get_hostname(),
            "port": pid.get_open_port()
        }
        result = pid.create_postgres_instance('tests_postgraas_test_instance_name', db_credentials)
        self.assertEqual(result, 'fy8rfsufusgsufbvluluivhhvsbr')

    def test_create_postgres_instance_api(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_create_postgres_instance_api",
            "db_name": "test_create_postgres_instance",
            "db_username": "db_user",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials)
        headers = {'Content-Type': 'application/json'}
        result = self.app.post('/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials))
        created_db = json.loads(result.data)
        self.assertEqual(created_db["db_name"], 'test_create_postgres_instance')
        self.delete_instance_by_name(db_credentials)

    def test_delete_postgres_instance_api(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_create_postgres_instance_api",
            "db_name": "test_create_postgres_instance",
            "db_username": "db_user",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials)
        headers = {'Content-Type': 'application/json'}
        result = self.app.post('/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials))
        created_db = json.loads(result.data)
        delete_result = self.app.delete('/api/v2/postgraas_instances/' + str(created_db["postgraas_instance_id"]))
        deleted_db = json.loads(delete_result.data)
        self.assertEqual(deleted_db["status"], 'success')
        self.delete_instance_by_name(db_credentials)

    @patch.object(docker.Client, 'create_container', return_value={'Id': 'fy8rfsufusgsufbvluluivhhvsbr'})
    def test_create_postgres_instance_fail(self, mockerclientcreate):
        db_credentials = {
            "db_name": 'test_db_name',
            "db_username": 'test_db_username',
            "db_pwd": 'test_db_pwd',
            "host": pid.get_hostname(),
            "port": pid.get_open_port()
        }
        self.assertRaises(APIError, pid.create_postgres_instance, 'test_instance_name', db_credentials)

    def test_create_postgres_instance_name_exists(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_my_postgraas_twice",
            "db_name": "my_db",
            "db_username": "db_user",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials)
        headers = {'Content-Type': 'application/json'}
        first = self.app.post('/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials))
        second = self.app.post('/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials))
        self.assertEqual(second.data, json.dumps({"msg": "postgraas_instance_name already exists tests_postgraas_my_postgraas_twice"})+"\n")
        self.delete_instance_by_name(db_credentials)



if __name__ == '__main__':
    unittest.main()
