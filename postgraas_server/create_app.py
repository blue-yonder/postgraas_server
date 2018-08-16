import logging

from flask import Flask
from flask_restful import Api
from raven.contrib.flask import Sentry

import postgraas_server
from postgraas_server.backends import get_backend
from postgraas_server.configuration import get_application_config, get_meta_db_config_path
from postgraas_server.management_resources import DBInstanceResource, DBInstanceCollectionResource, db

INT_OPTIONS = [
    'SQLALCHEMY_POOL_RECYCLE', 'SQLALCHEMY_POOL_SIZE', 'SQLALCHEMY_POOL_TIMEOUT',
    'SQLALCHEMY_MAX_OVERFLOW'
]

sentry = Sentry(logging=True, level=logging.WARN, wrap_wsgi=True, logging_exclusions=())


def create_app(config):
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = get_meta_db_config_path(config)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['BUNDLE_ERRORS'] = True
    app_config = get_application_config(config)

    for key in app_config:
        app.config[key.upper()] = int(app_config[key]) if key.upper() in INT_OPTIONS else app_config[key]
    app.config['SENTRY_INCLUDE_PATHS'] = [
        'postgraas_server',
    ]
    app.config['SENTRY_RELEASE'] = postgraas_server.__version__
    sentry.init_app(app)

    restful_api = Api(app)
    restful_api.add_resource(DBInstanceResource, "/api/v2/postgraas_instances/<int:id>")
    restful_api.add_resource(DBInstanceCollectionResource, "/api/v2/postgraas_instances")
    db.init_app(app)
    app.postgraas_backend = get_backend(config)

    @app.route('/health')
    def health():
        return "ok"

    return app
