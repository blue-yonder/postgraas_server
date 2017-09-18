import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


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
    con = _create_pg_connection(config)
    cur = con.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname='{}';".format(db_name))
    db_exists = cur.fetchone() is not None
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname='{}';".format(db_user))
    user = cur.fetchone()
    user_exists = user is not None
    return db_exists or user_exists


def create_postgres_db(connection_dict, config):
    if check_db_or_user_exists(connection_dict["db_name"], connection_dict["db_username"], config):
        raise ValueError("db or user already exists")
    con = _create_pg_connection(config)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    create_role = "CREATE USER {db_username} WITH PASSWORD '{db_pwd}';".format(**connection_dict)
    drop_role = "DROP ROLE {db_username};".format(**connection_dict)
    grant_role = 'GRANT {db_username} TO "{postgraas_user}";'.format(
        db_username=connection_dict['db_username'], postgraas_user=config['username'].split('@')[0]
    )
    create_database = "CREATE DATABASE {db_name} OWNER {db_username};".format(**connection_dict)
    try:
        cur.execute(create_role)
        cur.execute(grant_role)
    except psycopg2.ProgrammingError as e:
        raise ValueError(e.args[0])
    # cleanup role in case database creation fails
    # saidly 'CREATE DATABASE' cannot run inside a transaction block
    try:
        cur.execute(create_database)
    except psycopg2.ProgrammingError as e:
        cur.execute(drop_role)
        raise ValueError(e.args[0])


def delete_database(db_name, config):
    con = _create_pg_connection(config)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    try:
        cur.execute('''DROP DATABASE "{}";'''.format(db_name))
    except psycopg2.ProgrammingError as e:
        raise ValueError(e.args[0])



def delete_user(username, config):
    con = _create_pg_connection(config)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    try:
        cur.execute('''DROP USER "{}";'''.format(username))
    except psycopg2.ProgrammingError as e:
        raise ValueError(e.args[0])