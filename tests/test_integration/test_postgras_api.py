__author__ = 'osboxes'

import unittest
from mock import patch
import json
import postgraas_server.postgraas_api as papi
import postgraas_server.postgres_instance_driver as pid
import docker
from docker.errors import APIError


class TestPostgraasApi(unittest.TestCase):

    def get_postgraas_by_name(self, name):
        headers = {'Content-Type': 'application/json'}
        list = self.app.get('/api/v2/postgraas_instances', headers=headers)
        #print list.data
        for instance in json.loads(list.data):
            #print instance
            if instance["postgraas_instance_name"] == name:
                return instance["id"]

    def delete_instance_by_name(self, db_credentials):
        id = self.get_postgraas_by_name(db_credentials["postgraas_instance_name"])
        print id
        print self.app.delete('/api/v2/postgraas_instances/' + str(id))

    def setUp(self):
        papi.app.config['TESTING'] = True
        self.app = papi.app.test_client()

    @patch.object(docker.Client, 'create_container', return_value={'Id': 'fy8rfsufusgsufbvluluivhhvsbr'})
    @patch.object(docker.Client, 'start', return_value=None)
    def test_create_postgres_instance(self, mockerclientstart, mockerclientcreate):
        print mockerclientcreate
        print mockerclientstart
        db_credentials = {
            "db_name": 'test_db_name',
            "db_username": 'test_db_username',
            "db_pwd": 'test_db_pwd',
            "host": pid.get_hostname(),
            "port": pid.get_open_port()
        }
        result = pid.create_postgres_instance('test_instance_name', db_credentials)
        self.assertEqual(result, 'fy8rfsufusgsufbvluluivhhvsbr')

    def test_create_postgres_instance_api(self):
        db_credentials = {
            "postgraas_instance_name": "test_create_postgres_instance_api",
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
            "postgraas_instance_name": "test_create_postgres_instance_api",
            "db_name": "test_create_postgres_instance",
            "db_username": "db_user",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials)
        headers = {'Content-Type': 'application/json'}
        result = self.app.post('/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials))
        created_db = json.loads(result.data)
        print created_db
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
            "postgraas_instance_name": "my_postgraas_twice",
            "db_name": "my_db",
            "db_username": "db_user",
            "db_pwd": "secret"
        }
        self.delete_instance_by_name(db_credentials)
        headers = {'Content-Type': 'application/json'}
        first = self.app.post('/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials))
        second = self.app.post('/api/v2/postgraas_instances', headers=headers, data=json.dumps(db_credentials))
        print second.data
        self.assertEqual(second.data, json.dumps({"msg": "postgraas_instance_name already exists my_postgraas_twice"}))
        self.delete_instance_by_name(db_credentials)



if __name__ == '__main__':
    unittest.main()
