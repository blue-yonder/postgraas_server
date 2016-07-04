__author__ = 'sebastianneubauer'
import datetime
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import fields, Resource, marshal_with, Api, reqparse
from docker.errors import APIError
import logging
import docker
import postgres_instance_driver as pg
logger = logging.getLogger(__name__)


db = SQLAlchemy()


class DBInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    postgraas_instance_name = db.Column(db.String(100))
    creation_timestamp = db.Column(db.DateTime)
    db_name = db.Column(db.String(100))
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    hostname = db.Column(db.String(50))
    port = db.Column(db.Integer)
    container_id = db.Column(db.String(100))

    def __init__(self, postgraas_instance_name, db_name, username, password, hostname, port, container_id):
        self.postgraas_instance_name = postgraas_instance_name
        self.creation_timestamp = datetime.datetime.now()
        self.db_name = db_name
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.container_id = container_id

    def __repr__(self):
        return '<PGName {} User {} Docker_id {}>'.format(self.postgraas_instance_name, self.username, self.container_id)


db_instance_marshaller = {
    'id': fields.Integer,
    'postgraas_instance_name': fields.String,
    'creation_timestamp': fields.DateTime(dt_format='iso8601'),
    'db_name': fields.String,
    'username': fields.String,
    'password': fields.String,
    'hostname': fields.String,
    'port': fields.String,
    'container_id': fields.String,
}


class DBInstanceResource(Resource):

    @marshal_with(db_instance_marshaller)
    def get(self, id):
        entity = DBInstance.query.get(id)
        return entity

    def delete(self, id):
        c = docker.Client(base_url='unix://var/run/docker.sock',
                            version='auto',
                            timeout=10)
        entity = DBInstance.query.get(id)
        if entity:
            try:
                container_info = c.inspect_container(entity.container_id)
                print container_info
            except APIError as e:
                if e.response.status_code == 404:
                    logger.warning("conatiner {} doe not exist, how could that happen?".format(entity.container_id))
                    db.session.delete(entity)
                    db.session.commit()
                    return {'status': 'sucess', 'msg': 'deleted postgraas instance, but container was not found...'}
            try:
                pg.delete_postgres_instance(entity.container_id)
            except APIError as e:
                logger.warning("error deleting conatiner {}: {}".format(entity.container_id, str(e)))
                return {'status': 'failed', 'msg': str(e)}
            db.session.delete(entity)
            db.session.commit()
            return {'status': 'success', 'msg': 'deleted postgraas instance'}
        else:
            return {'status': 'failed', 'msg': 'Postgraas instance does not exist {}'.format(id)}



class DBInstanceListResource(Resource):

    @marshal_with(db_instance_marshaller)
    def get(self):
        all = DBInstance.query.all()
        return all

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('postgraas_instance_name', required=True, type=str, help='name of the postgraas instance')
        parser.add_argument('db_name', required=True, type=str, help='name of the db')
        parser.add_argument('db_username', required=True, type=str, help='username of the db')
        parser.add_argument('db_pwd', required=True, type=str, help='pass of the db user')
        args = parser.parse_args()
        db_credentials = {
            "db_name": args['db_name'],
            "db_username": args['db_username'],
            "db_pwd": args['db_pwd'],
            "host": pg.get_hostname(),
            "port": pg.get_open_port()
        }
        if DBInstance.query.filter_by(postgraas_instance_name=args['postgraas_instance_name']).first():
            return {'msg': "postgraas_instance_name already exists {}".format(args['postgraas_instance_name']) }
        try:
            db_credentials['container_id'] = pg.create_postgres_instance(args['postgraas_instance_name'], db_credentials)
        except APIError as e:
            return {'msg': str(e)}
        db_entry = DBInstance(postgraas_instance_name=args['postgraas_instance_name'],
                              db_name=args['db_name'],
                              username=args['db_username'],
                              password="",
                              hostname=db_credentials['host'],
                              port=db_credentials['port'],
                              container_id=db_credentials['container_id'])
        db.session.add(db_entry)
        db.session.commit()
        db_credentials["postgraas_instance_id"] = db_entry.id
        return db_credentials