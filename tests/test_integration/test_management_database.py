import unittest

import os

import postgraas_server.configuration as configuration
from postgraas_server.create_app import create_app
from postgraas_server.management_database import is_sane_database


class TestManagementDatabase(unittest.TestCase):
    def setUp(self):
        self.module_path = os.path.abspath(os.path.dirname(__file__))
        self.this_app = create_app(
            configuration.get_config(os.path.join(self.module_path, 'application.cfg'))
        )
        self.this_app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        self.this_app.use_reloader = False
        self.this_app.config['TESTING'] = True

    def tearDown(self):
        from postgraas_server.management_resources import db
        with self.this_app.app_context():
            db.drop_all()

    def test_is_sane_database(self):
        from postgraas_server.management_resources import db
        with self.this_app.app_context():
            db.drop_all()
            db.create_all()
            is_sane = is_sane_database(db.Model, db.session)

        self.assertEqual(True, is_sane)

    def test_is_not_sane_database(self):
        from postgraas_server.management_resources import db
        with self.this_app.app_context():
            is_sane = is_sane_database(db.Model, db.session)
        self.assertEqual(False, is_sane)


if __name__ == '__main__':
    unittest.main()
