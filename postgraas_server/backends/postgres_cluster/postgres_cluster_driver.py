import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.sql import SQL, Identifier


def _create_pg_connection(config):
    if 'server' in config:
        username = '@'.join([config['username'], config['server']])
    else:
        username = config['username']
    return psycopg2.connect(
        database=config['database'],
        user=username,
        host=config['host'],
        port=config['port'],
        password=config['password'],
    )


def check_db_or_user_exists(db_name, db_user, config):
    with _create_pg_connection(config) as con:
        with con.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname=%s;", (db_name, ))
            db_exists = cur.fetchone() is not None
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname=%s;", (db_user, ))
            user = cur.fetchone()
            user_exists = user is not None
            return db_exists or user_exists


def create_postgres_db(connection_dict, config):
    if check_db_or_user_exists(connection_dict["db_name"], connection_dict["db_username"], config):
        raise ValueError("db or user already exists")
    with _create_pg_connection(config) as con:
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with con.cursor() as cur:
            try:
                cur.execute(SQL("CREATE USER {} WITH PASSWORD %s;").format(
                    Identifier(connection_dict['db_username']),
                ), (
                    connection_dict['db_pwd'],
                ))
                cur.execute(SQL("GRANT {} TO {};").format(
                    Identifier(connection_dict['db_username']),
                    Identifier(config['username']),
                ))
            except psycopg2.ProgrammingError as e:
                raise ValueError(e.args[0])
            # cleanup role in case database creation fails
            # sadly 'CREATE DATABASE' cannot run inside a transaction block
            try:
                cur.execute(SQL("CREATE DATABASE {} OWNER {};").format(
                    Identifier(connection_dict['db_name']),
                    Identifier(connection_dict['db_username']),
                ))
            except psycopg2.ProgrammingError as e:
                cur.execute(SQL("DROP USER {};").format(
                    Identifier(connection_dict['db_username']),
                ))
                raise ValueError(e.args[0])


def get_normalized_username(username):
    return username.split('@')[0]


def delete_database(db_name, config):
    with _create_pg_connection(config) as con:
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with con.cursor() as cur:
            try:
                cur.execute(SQL('DROP DATABASE {};').format(
                    Identifier(db_name),
                ))
            except psycopg2.ProgrammingError as e:
                raise ValueError(e.args[0])


def delete_user(username, config):
    with _create_pg_connection(config) as con:
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with con.cursor() as cur:
            try:
                cur.execute(SQL('DROP USER {};').format(
                   Identifier(get_normalized_username(username)),
                ))
            except psycopg2.ProgrammingError as e:
                raise ValueError(e.args[0])
