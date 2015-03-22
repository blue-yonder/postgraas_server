__author__ = 'sebastianneubauer'

DB_PATH = 'postgresql://postgraas:postgraas12@localhost/postgraas'

def init_db(db_credentials):
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from postgraas_server.postgraas_api import db
    db.drop_all()
    db.create_all()
    from postgraas_server.postgraas_api import DBInstance
    admin = DBInstance(postgraas_instance_name='PostgraasMetaDB',
                      db_name=db_credentials["db_name"],
                      username=db_credentials["db_username"],
                      password=db_credentials["db_pwd"],
                      hostname=db_credentials["host"],
                      port=db_credentials["host"],
                      container_id=db_credentials['container_id'])
    db.session.add(admin)
    db.session.commit()