import unittest
import os
from mock import patch, MagicMock, Mock

import json
import postgraas_server.configuration as configuration
from postgraas_server.create_app import create_app
import postgraas_server.postgres_instance_driver as pid
import docker
from .utils import wait_for_postgres_listening


class TestPostgraasApi(unittest.TestCase):

    def get_postgraas_by_name(self, name):
        headers = {'Content-Type': 'application/json'}
        list = self.app.get('/api/v2/postgraas_instances', headers=headers)
        for instance in json.loads(list.data):
            if instance["postgraas_instance_name"] == name:
                return instance["id"]

    def delete_instance_by_name(self, db_credentials):
        id = self.get_postgraas_by_name(db_credentials["postgraas_instance_name"])
        db_pwd = db_credentials["db_pwd"]
        headers = {'Content-Type': 'application/json'}
        self.app.delete('/api/v2/postgraas_instances/' + str(id),
                        data=json.dumps({'db_pwd': db_pwd}), headers=headers)

    def delete_all_test_postgraas_container(self):
        c = pid._docker_client()
        for container in c.containers.list():
            if container.name.startswith("tests_postgraas_"):
                container.remove(force=True)

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

    def test_create_postgres_instance(self):
        db_credentials = {
            "db_name": 'test_db_name',
            "db_username": 'test_db_username',
            "db_pwd": 'test_db_pwd',
            "host": pid.get_hostname(),
            "port": pid.get_open_port()
        }
        mock_c = MagicMock()
        mock_c.id = 'fy8rfsufusgsufbvluluivhhvsbr'
        mock_create = Mock(return_value = mock_c)
        with patch.object(docker.models.containers.ContainerCollection, 'create', mock_create):
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

    def test_create_docker_fails(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_create_postgres_instance_api",
            "db_name": "test_create_postgres_instance",
            "db_username": "db_user",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials)
        headers = {'Content-Type': 'application/json'}

        def raise_apierror(*args, **kwargs):
            raise docker.errors.NotFound('let create fail')

        with patch.object(docker.models.containers.ContainerCollection, 'create', raise_apierror):
            result = self.app.post('/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials))
        created_db = json.loads(result.data)
        self.assertTrue('let create fail' in created_db["msg"], 'unexpected error message for docker create failure')

    def test_delete_postgres_instance_api(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_delete_postgres_instance_api",
            "db_name": "test_create_postgres_instance",
            "db_username": "db_user",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials)
        headers = {'Content-Type': 'application/json'}
        result = self.app.post('/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials))
        created_db = json.loads(result.data)
        wait_success = wait_for_postgres_listening(created_db['container_id'])
        self.assertTrue(wait_success, 'postgres did not come up within 10s (or unexpected docker image log output)')
        delete_result = self.app.delete('/api/v2/postgraas_instances/' + str(created_db["postgraas_instance_id"]),
                                        data=json.dumps({'db_pwd': 'wrong_password'}), headers=headers)
        deleted_db = json.loads(delete_result.data)

        self.assertEqual(deleted_db["status"], 'failed')
        self.assertTrue('password authentication failed' in deleted_db['msg'], 'unexpected message for wrong password')

        def raise_apierror(*args, **kwargs):
            raise docker.errors.NotFound('let remove fail')

        with patch.object(docker.models.containers.Container, 'remove', raise_apierror):
            delete_result = self.app.delete('/api/v2/postgraas_instances/' + str(created_db["postgraas_instance_id"]),
                                            data=json.dumps({'db_pwd': db_credentials['db_pwd']}), headers=headers)
            deleted_db = json.loads(delete_result.data)
            self.assertEqual(deleted_db["status"], 'failed')
            self.assertTrue('let remove fail' in deleted_db['msg'], 'unexpected error message on docker rm failure')

        delete_result = self.app.delete('/api/v2/postgraas_instances/' + str(created_db["postgraas_instance_id"]),
                                        data=json.dumps({'db_pwd': db_credentials['db_pwd']}), headers=headers)
        deleted_db = json.loads(delete_result.data)
        self.assertEqual(deleted_db["status"], 'success')

    def test_delete_docker_notfound(self):
        db_credentials = {
            "postgraas_instance_name": "tests_postgraas_test_delete_docker_notfound",
            "db_name": "test_create_postgres_instance",
            "db_username": "db_user",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials)
        headers = {'Content-Type': 'application/json'}
        result = self.app.post('/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials))
        created_db = json.loads(result.data)
        wait_success = wait_for_postgres_listening(created_db['container_id'])
        self.assertTrue(wait_success, 'postgres did not come up within 10s (or unexpected docker image log output)')

        def raise_not_found(*args, **kwargs):
            raise docker.errors.NotFound('raise for testing from mock')

        with patch.object(docker.models.containers.ContainerCollection, 'get', raise_not_found):
            res = self.app.delete('/api/v2/postgraas_instances/' + str(created_db["postgraas_instance_id"]),
                                  data=json.dumps({'db_pwd': db_credentials['db_pwd']}), headers=headers)
            res = json.loads(res.data)
        self.assertEqual(res['status'], 'success')
        self.assertTrue('deleted postgraas instance, but container was not found' in res['msg'], 'unexpected delete message')

    def test_delete_notfound(self):
        headers = {'Content-Type': 'application/json'}
        res = self.app.delete('/api/v2/postgraas_instances/123456789',
                              data=json.dumps({'db_pwd': '123'}), headers=headers)
        res = json.loads(res.data)
        self.assertEqual(res['status'], 'failed')
        self.assertTrue("123456789" in res['msg'], 'unexpected error message')

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
        self.assertRaises(ValueError, pid.create_postgres_instance, 'test_instance_name', db_credentials)
        pid.delete_postgres_instance(id0)
        self.assertFalse(pid.check_container_exists(id0), "container exists after it was deleted")

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

    def test_return_postgres_instance_api(self):
        db_credentials = {
            u"postgraas_instance_name": u"tests_postgraas_test_return_postgres_instance_api",
            u"db_name": u"test_return_postgres_instance",
            u"db_username": u"db_user",
            u"db_pwd": u"secret"
        }
        self.delete_instance_by_name(db_credentials)
        headers = {'Content-Type': 'application/json'}
        result = self.app.post('/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials))
        created_db = json.loads(result.data)
        created_db_id = created_db['postgraas_instance_id']
        actual = self.app.get('api/v2/postgraas_instances/{}'.format(created_db_id), headers=headers)
        self.assertEqual(actual.status_code, 200)
        actual_data = json.loads(actual.data)
        actual_data.pop('container_id')
        actual_data.pop('port')
        actual_data.pop('creation_timestamp')
        expected = {
            u'postgraas_instance_name': u'tests_postgraas_test_return_postgres_instance_api',
            u'db_name': u'test_return_postgres_instance',
            u'username': u'db_user',
            u'password': u'',
            u'hostname': u'not imlemented yet',
            u'id': created_db_id,
        }
        self.assertDictEqual(actual_data, expected)

        self.delete_instance_by_name(db_credentials)


if __name__ == '__main__':
    unittest.main()
