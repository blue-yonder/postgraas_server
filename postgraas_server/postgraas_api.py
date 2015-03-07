from logging import basicConfig

__author__ = 'neubauer'
import datetime
from flask import Flask, request, jsonify
import docker
from docker.errors import APIError
import hashlib
import socket
import postgraas_server.management_database as database
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import fields, Resource, marshal_with, Api, reqparse


import logging

logger = logging.getLogger(__name__)


app = Flask(__name__)
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = database.DB_PATH


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
        entity = DBInstance.query.get(id)
        if entity:
            try:
                delete_postgres_instance(entity.container_id)
            except APIError as e:
                logger.warning("error deleting conatiner {}: {}".format(entity.container_id, e.message))
            db.session.delete(entity)
            db.session.commit()



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
            "host": get_hostname(),
            "port": get_open_port()
        }
        try:
            db_credentials['container_id'] = create_postgres_instance(db_credentials)
        except Exception as e:
            return {'msg': e.message}
        db_entry = DBInstance(postgraas_instance_name=args['postgraas_instance_name'],
                              db_name=args['db_name'],
                              username=args['db_username'],
                              password=args['db_pwd'],
                              hostname=db_credentials['host'],
                              port=db_credentials['port'],
                              container_id=db_credentials['container_id'])
        #all = DBInstance.query.all()
        print db_entry
        db.session.add(db_entry)
        db.session.commit()
        return db_credentials

restful_api = Api(app)
restful_api.add_resource(DBInstanceResource, "/api/v1/postgraas_instances/<int:id>")
restful_api.add_resource(DBInstanceListResource, "/api/v1/postgraas_instances")


def get_unique_id(connection_dict):
    return hashlib.sha1(str(frozenset(connection_dict.items()))).hexdigest()

def get_open_port():
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("",0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port

def create_postgres_instance(connection_dict):
    #docker run -d -p 5432:5432 -e POSTGRESQL_USER=test -e POSTGRESQL_PASS=oe9jaacZLbR9pN -e POSTGRESQL_DB=test orchardup/postgresql
    c = docker.Client(base_url='unix://var/run/docker.sock',
                  timeout=10)
    environment = {
        "POSTGRESQL_USER": connection_dict['db_username'],
        "POSTGRESQL_PASS": connection_dict['db_pwd'],
        "POSTGRESQL_DB": connection_dict['db_name']
    }
    internal_port = 5432
    container_info = c.create_container('postgres', ports=[internal_port], environment=environment)
    container_id = container_info['Id']
    port_dict = {internal_port: connection_dict['port']}
    c.start(container_id, port_bindings=port_dict)
    return container_id

def delete_postgres_instance(container_id):
    #docker run -d -p 5432:5432 -e POSTGRESQL_USER=test -e POSTGRESQL_PASS=oe9jaacZLbR9pN -e POSTGRESQL_DB=test orchardup/postgresql
    c = docker.Client(base_url='unix://var/run/docker.sock',
                  timeout=10)
    print c.stop(container_id)
    return True

def get_hostname():
    #return socket.gethostbyname(socket.gethostname())
    return "weather-test1"


@app.route("/postgraas/one_db_please")
def hello():
    db_credentials = {
    "db_name": request.args.get('db_name', ''),
    "db_username": request.args.get('db_username', ''),
    "db_pwd": request.args.get('db_pwd', ''),
    "host": get_hostname(),
    "port": get_open_port()
    }
    db_credentials['db_id'] = get_unique_id(db_credentials)
    db_credentials['container_id'] = create_postgres_instance(db_credentials)
    logger.info('created db {}'.format(db_credentials))
    return jsonify(db_credentials)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
