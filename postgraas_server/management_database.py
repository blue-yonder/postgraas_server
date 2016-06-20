__author__ = 'sebastianneubauer'



def init_db(db_credentials, postgraas_app):
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from postgraas_server.postgraas_api import db
    with postgraas_app.app_context():
        db.drop_all()
        db.create_all()
        #maybe this is a bad idea?
        #from postgraas_server.management_resources import DBInstance
        #admin = DBInstance(postgraas_instance_name='PostgraasMetaDB',
        #                  db_name=db_credentials["db_name"],
        #                  username=db_credentials["db_username"],
        #                  password=db_credentials["db_pwd"],
        #                  hostname=db_credentials["host"],
        #                  port=db_credentials["port"],
        #                  container_id=db_credentials['container_id'])
        #db.session.add(admin)
        #db.session.commit()