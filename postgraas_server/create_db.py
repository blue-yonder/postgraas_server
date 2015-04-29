__author__ = 'sebastianneubauer'

from postgraas_server.management_database import init_db
import postgres_instance_driver as pg


def create_db_container():
    db_credentials = {
            "db_name": 'postgraas',
            "db_username": 'postgraas',
            "db_pwd": 'postgraas12',
            "host": 'localhost',
            "port": 5432
        }
    try:
        db_credentials['container_id'] = pg.create_postgres_instance('postgraas_master_db', db_credentials)
    except ValueError as e:
        print "warning container already exists"
        postrgaas_db = pg.get_container_by_name('postgraas_master_db')
        db_credentials['container_id'] = postrgaas_db['Id']
    return db_credentials


def main():
    from postgraas_server import postgraas_api
    db_credentials = create_db_container()
    init_db(db_credentials, postgraas_api.app)


if __name__ == '__main__':
    main()