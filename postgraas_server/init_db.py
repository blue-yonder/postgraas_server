from postgraas_server.management_database import init_db
import postgres_instance_driver as pg
from postgraas_server.configuration import get_config


def main():
    from postgraas_server import postgraas_api
    config = get_config()
    db_credentials = {
            "db_name": config.get('metadb', 'db_name'),
            "db_username": config.get('metadb', 'db_username'),
            "db_pwd": config.get('metadb', 'db_pwd'),
            "host": config.get('metadb', 'host'),
            "port": config.get('metadb', 'port')
        }
    pg.wait_for_postgres(db_credentials['db_name'], db_credentials['db_username'], db_credentials['db_pwd'],
                          db_credentials['host'], db_credentials['port'])
    print "initializing db"
    init_db(db_credentials, postgraas_api.app)


if __name__ == '__main__':
    main()
