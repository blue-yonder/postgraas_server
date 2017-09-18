from postgraas_server.backends.docker import postgres_instance_driver as pg
from postgraas_server.configuration import get_config
from postgraas_server.utils import wait_for_postgres


def create_db_container():
    config = get_config()
    db_credentials = {
        "db_name": config.get('metadb', 'db_name'),
        "db_username": config.get('metadb', 'db_username'),
        "db_pwd": config.get('metadb', 'db_pwd'),
        "host": config.get('metadb', 'host'),
        "port": config.get('metadb', 'port')
    }
    if pg.check_container_exists('postgraas_master_db'):
        print "warning container already exists"
        postgraas_db = pg.get_container_by_name('postgraas_master_db')
        db_credentials['container_id'] = postgraas_db.id
    else:
        db_credentials['container_id'] = pg.create_postgres_instance(
            'postgraas_master_db', db_credentials
        )
    return db_credentials


def main():
    print "creating container for the management db"
    db_credentials = create_db_container()
    wait_for_postgres(
        db_credentials['db_name'], db_credentials['db_username'], db_credentials['db_pwd'],
        db_credentials['host'], db_credentials['port']
    )


if __name__ == '__main__':
    main()
