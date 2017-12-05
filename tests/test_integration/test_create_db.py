from subprocess import check_call

import os
import pytest

import postgraas_server.backends.docker.postgres_instance_driver as pid
from postgraas_server import init_db
from postgraas_server.backends.docker import create_db

this_dir = os.path.dirname(__file__)


@pytest.yield_fixture
def cov_runner():
    # pretty hacky fixture to measure coverage of python scripts started as subprocess.
    # * run the script via 'coverage run', not via python
    # * move the created .coverage files to ../.. so they are merged with the others
    check_call("rm -f .coverage.*", shell=True, cwd=this_dir)

    def run(script):
        command = "coverage run --branch --source ../.. -p {}".format(script)
        check_call(command, cwd=this_dir, shell=True)

    yield run
    check_call("mv .coverage.* ../..", shell=True, cwd=this_dir)


def test_create_init_db(cov_runner):
    # test the standalone 'create_db' and 'init_db' scripts.
    if pid.check_container_exists('postgraas_master_db'):
        pid.delete_postgres_instance('postgraas_master_db')
    create_db_file = create_db.__file__
    cov_runner(create_db_file)
    # also check the path where the container already exists:
    cov_runner(create_db_file)

    init_db_file = init_db.__file__
    cov_runner(init_db_file)
