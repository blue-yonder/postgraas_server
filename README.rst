================
postgraas_server
================

.. image:: https://travis-ci.org/blue-yonder/postgraas_server.svg?branch=master
    :target: https://travis-ci.org/blue-yonder/postgraas_server


.. image:: https://coveralls.io/repos/github/blue-yonder/postgraas_server/badge.svg?branch=master
    :target: https://coveralls.io/github/blue-yonder/postgraas_server?branch=master


Postgraas is a super simple PostgreSQL-as-a-service


What is Postgraas?
==================

Postgraas offers `CRUD <https://de.wikipedia.org/wiki/CRUD>`_ operations for complete PostgreSQL database instances via a simple REST api.
The database instances are docker containers and the API server is a few hundred LoC Flask application.
It is not meant as a production ready solution, but more as a proof-of-concept to spread the idea of creating "as-a-service" services easily yourself and should inspire you to start working on your own cloud infrastructure today.
But in fact, it proofs the concept very well and it turned out to be super useful for delivering a PostgreSQL instance if you need one fast, e.g. for integration tests, for playing around with fancy ShowHN projects or other experiments.
The CRUD management via REST api is of course also a necessary prerequisite for building an automated continuous delivery pipeline for a modern software project.


Installation
============
You can find detailed instructions in the `docs <http://postgraas-server.readthedocs.io/en/latest/installation.html>`_

Install via pip::

    pip install postgraas_server

Start the WSGI api server for example via gunicorn::

    pip install gunicorn
    gunicorn -w 4 -b 0.0.0.0:8080 postgraas_server.postgraas_api:app


Usage
=====

We need to send all the required parameters for the creation as an http request.
This is quite convenient by creating a file e.g. ``my_postgraas.json``::

    {
        "postgraas_instance_name": "my_postgraas",
        "db_name": "my_db",
        "db_username": "db_user",
        "db_pwd": "secret"
    }

and making a POST request to the collection resource with curl::

    curl -H "Content-Type: application/json" -X POST --data @my_postgraas.json http://localhost:8080/api/v2/postgraas_instances

now your instance is created and as a response you get the details of your instance::

    {
         "postgraas_instance_id": 1,
         "container_id": "193f0d94d49fa26626fdbdb583e9453f923468b01eac59207b4852831a105c03",
         "db_pwd": "secret",
         "host": "not implemented yet",
         "db_name": "my_db",
         "db_username": "db_user",
         "port": 54648
    }

We are now able to connect to the database for example via ``psql``::

    psql -h localhost -p 54648 -U db_user my_db

Awesome, isn’t it?

Development
===========

You can follow the next steps in order to host postgraas_server locally and be able to develop features or bug fixes:

Clone repository::

    git clone https://github.com/blue-yonder/postgraas_server

Install all the project dependencies::

    pip install -r requirements_dev.txt
    pip install -r requirements_docker.in
    pip install -r requirements_prometheus.in 
    pip install gunicorn
    pip install -e .

Docker
------

Pull the right docker image::

    docker pull postgres:9.4

Your application.cfg file should look like this::

    {
        "metadb":
        {
            "db_name": "postgres",
            "db_username": "postgres",
            "db_pwd": "mysecret",
            "host": "localhost",
            "port": "5432"
        },
        "backend":
        {
            "type": "docker"
        }
    }

Initialize a postgres DB within a docker container::

    sh setup_integration_test_docker.sh

Run a Docker container with the postgres image::

    postgraas_init

Postgres Cluster
----------------

If you don't want to use Docker as the backend you could create a local postgres cluster

Your application.cfg file should look like this::

    {
        "metadb":
        {
            "db_name": "postgres",
            "db_username": "postgres",
            "db_pwd": "mysecret",
            "host": "localhost",
            "port": "5432"
        },
        "backend":
        {
            "type": "pg_cluster",
            "database": "postgres",
            "username": "postgres",
            "password": "mysecret",
            "host": "localhost",
            "port": "5432"
        }
    }

Run postgres server::

    postgres -D /usr/local/var/postgres

Execute application locally
---------------------------

Run the Flask application by executing this command::

    python postgraas_server/postgraas_api.py

After this your application should be started and you can perform GET/POST/DELETE actions to this endppoint::

    http://localhost:5000/api/v2/postgraas_instances

Alternatively, you can run your unit and integration tests to verify your new code::

    pytest tests/
