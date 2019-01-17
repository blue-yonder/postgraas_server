from postgraas_server.configuration import get_config, get_user, get_password
from postgraas_server.management_database import init_db
from postgraas_server.utils import wait_for_postgres


def main():
    from postgraas_server import postgraas_api
    config = get_config()
    db_credentials = {
        "db_name": config['metadb']['db_name'],
        "db_username": get_user(config),
        "db_pwd": get_password(config),
        "host": config['metadb']['host'],
        "port": config['metadb']['port']
    }

    wait_for_postgres(
        db_credentials['db_name'], db_credentials['db_username'], db_credentials['db_pwd'],
        db_credentials['host'], db_credentials['port']
    )
    print("initializing db")
    init_db(postgraas_api.app)


if __name__ == '__main__':
    main()
