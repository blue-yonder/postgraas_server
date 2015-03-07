__author__ = 'sebastianneubauer'

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DB_PATH = 'postgresql://postgraas:postgraas12@localhost/postgraas'

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from postgraas_server.postgraas_api import db
    db.drop_all()
    db.create_all()
    from postgraas_server.postgraas_api import DBInstance
    admin = DBInstance(postgraas_instance_name='PostgraasMetaDB',
                      db_name='postgraas',
                      username='postgraas',
                      password='postgraas12',
                      hostname='localhost',
                      port=5432,
                      container_id='not implented yet...')
    db.session.add(admin)
    db.session.commit()