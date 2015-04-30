__author__ = 'neubauer'
import logging
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import fields, Resource, marshal_with, Api, reqparse
import postgraas_server.management_database as database
from postgraas_server.management_resources import db
from postgraas_server.management_resources import DBInstanceResource, DBInstanceListResource


logger = logging.getLogger(__name__)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = database.DB_PATH


restful_api = Api(app)
restful_api.add_resource(DBInstanceResource,        "/api/v2/postgraas_instances/<int:id>")
restful_api.add_resource(DBInstanceListResource,    "/api/v2/postgraas_instances")
db.init_app(app)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
