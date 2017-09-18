import time

import psycopg2


def wait_for_postgres(dbname, user, password, host, port):
    """
    Try to connect to postgres every second, until it succeeds.
    """
    for i in range(540):
        try:
            psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
            return
        except psycopg2.OperationalError:
            print i, " ..waiting for db"
            time.sleep(1)
