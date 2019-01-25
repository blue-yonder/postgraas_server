# coding=utf-8

import contextlib
import json
import os

import psycopg2
from psycopg2.sql import SQL

from postgraas_server.configuration import get_user, get_password


CLUSTER_CONFIG = {
    "metadb": {
        "db_name": os.environ.get('PGDATABASE', 'postgres'),
        "db_username": os.environ.get('PGUSER', 'postgres'),
        "db_pwd": os.environ.get('PGPASSWORD', 'postgres'),
        "host": os.environ.get('PGHOST', 'localhost'),
        "port": os.environ.get('PGPORT', '5432'),
    }
}


@contextlib.contextmanager
def _get_db_con():
    with psycopg2.connect(
            database=CLUSTER_CONFIG['metadb']['db_name'],
            user=get_user(CLUSTER_CONFIG),
            host=CLUSTER_CONFIG['metadb']['host'],
            port=CLUSTER_CONFIG['metadb']['port'],
            password=get_password(CLUSTER_CONFIG),
    ) as con:
        yield con


def test_smoke(tmpdir):
    cfg = tmpdir.join('application.cfg')
    with open(cfg.strpath, "w") as fp:
        json.dump(CLUSTER_CONFIG, fp)

    with _get_db_con() as con:
        with con.cursor() as cur:
            cur.execute(SQL("DROP TABLE IF EXISTS db_instance"))
        con.commit()

    with tmpdir.as_cwd():
        import postgraas_server.init_db
        postgraas_server.init_db.main()

    with _get_db_con() as con:
        with con.cursor() as cur:
            cur.execute(SQL("SELECT * FROM db_instance"))
            assert 0 == len(cur.fetchall())

            cur.execute(SQL("DROP TABLE db_instance"))
        con.commit()
