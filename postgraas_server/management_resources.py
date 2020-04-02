import datetime
import logging

import psycopg2
from flask import current_app
from flask_restful import fields, Resource, marshal_with, reqparse, abort
from flask_sqlalchemy import SQLAlchemy

from postgraas_server.backends.exceptions import PostgraasApiException
from contextlib import closing

logger = logging.getLogger(__name__)

db = SQLAlchemy()


class DBInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    postgraas_instance_name = db.Column(db.String(100))
    creation_timestamp = db.Column(db.DateTime)
    db_name = db.Column(db.String(100))
    username = db.Column(db.String(500))
    password = db.Column(db.String(100))
    hostname = db.Column(db.String(500))
    port = db.Column(db.Integer)
    container_id = db.Column(db.String(100))

    def __init__(
            self,
            postgraas_instance_name,
            db_name,
            username,
            password,
            hostname,
            port,
            container_id=None
    ):
        self.postgraas_instance_name = postgraas_instance_name
        self.creation_timestamp = datetime.datetime.now()
        self.db_name = db_name
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.container_id = container_id

    def __repr__(self):
        return '<PGName {} User {} Docker_id {}>'.format(
            self.postgraas_instance_name, self.username, self.container_id
        )


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
        parser = reqparse.RequestParser()
        parser.add_argument('db_pwd', required=True, type=str, help='pass of the db user is needed to delete instance.')
        args = parser.parse_args()

        entity = DBInstance.query.get(id)
        if not entity:
            abort(404, status='failed', msg='Postgraas instance {} does not exist'.format(id))

        other_sessions = 0

        try:
            with closing(psycopg2.connect(
                    user=entity.username,
                    password=args['db_pwd'],
                    host=current_app.postgraas_backend.master_hostname,
                    port=entity.port,
                    dbname=entity.db_name
            )) as conn:
                cur = conn.cursor()
                cur.execute("select count(pid) from pg_stat_activity where datname = %s ;", (entity.db_name,))
                other_sessions = cur.fetchone()[0]-1
        except Exception as ex:
            return_code = 401 if 'authentication failed' in str(ex) else 500
            abort(return_code, status='failed', msg='Could not connect to postgres instance: {}'.format(str(ex)))

        if other_sessions > 0:
            abort(409, status='failed', msg='Database contains other {} active sessions. Please close or terminate all sessions before deleting'.format(other_sessions))

        if not current_app.postgraas_backend.exists(entity):
            logger.warning(
                "container {} does not exist, how could that happen?".format(entity.container_id)
            )
            db.session.delete(entity)
            db.session.commit()
            return {
                'status': 'success',
                'msg': 'deleted postgraas instance, but container was not found...'
            }

        try:
            current_app.postgraas_backend.delete(entity)
        except PostgraasApiException as e:
            logger.warning("error deleting container {}: {}".format(entity.container_id, str(e)))
            abort(500, status='failed', msg=str(e))
        db.session.delete(entity)
        db.session.commit()
        return {'status': 'success', 'msg': 'deleted postgraas instance'}


class DBInstanceCollectionResource(Resource):
    @marshal_with(db_instance_marshaller)
    def get(self):
        all = DBInstance.query.all()
        return all

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            'postgraas_instance_name',
            required=True,
            type=str,
            help='name of the postgraas instance'
        )
        parser.add_argument('db_name', required=True, type=str, help='Database name')
        parser.add_argument('db_username', required=True, type=str, help="Username of database user")
        parser.add_argument('db_pwd', required=True, type=str, help='Password of the database user')
        args = parser.parse_args()

        if not args['db_pwd']:
            abort(400, msg='The password may not be empty.')

        if args['db_username'] == "postgres" or  args['db_username'].startswith("postgres@"):
            abort(
                422,
                msg="username {} is backlisted".format(args['db_username'])
            )

        if DBInstance.query.filter_by(postgraas_instance_name=args['postgraas_instance_name']
                                      ).first():
            abort(
                409,
                msg="postgraas_instance_name already exists {}".format(
                    args['postgraas_instance_name']
                )
            )

        db_credentials = {
            "db_name": args['db_name'],
            "db_username": args['db_username'],
            "db_pwd": args['db_pwd'],
            "host": current_app.postgraas_backend.hostname,
            "port": current_app.postgraas_backend.port
        }

        db_entry = DBInstance(
            postgraas_instance_name=args['postgraas_instance_name'],
            db_name=args['db_name'],
            username=db_credentials['db_username'],
            password="",
            hostname=db_credentials['host'],
            port=db_credentials['port']
        )
        if current_app.postgraas_backend.exists(db_entry):
            abort(
                409,
                description="database or user already exists {}, {}".format(
                    args['db_name'], args['db_username']
                )
            )

        try:
            db_entry.container_id = current_app.postgraas_backend.create(db_entry, db_credentials)
        except PostgraasApiException as e:
            abort(500, msg=str(e))

        if '@' not in args['db_username']:
            try:
                username = '@'.join([args['db_username'], current_app.postgraas_backend.server])
            except (AttributeError, KeyError):
                username = args['db_username']
            db_entry.username = username

        db.session.add(db_entry)
        db.session.commit()
        db_credentials["container_id"] = db_entry.container_id
        db_credentials["postgraas_instance_id"] = db_entry.id
        db_credentials["db_username"] = db_entry.username
        return db_credentials, 201
