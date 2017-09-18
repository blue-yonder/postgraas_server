============
Installation
============

Prequisites
===========

* Tested on Debian/Ubuntu
* Python tested with 2.7
* Any wsgi server, tested with gunicorn
* recent pip & setuptools
* Docker Engine >= 1.12.0 (for the ``docker`` backend, see :ref:`postgraas-backends`)
* PostgreSQL Server (for the ``pg_cluster`` backend, see :ref:`postgraas-backends`)

Install via pip::

    pip install postgraas_server

Docker
======

Docker is the default backend of Postgraas. To use it,
pull the official postgres 9.4 docker `image <https://hub.docker.com/_/postgres/>`_ ::

    docker pull postgres:9.4

We need a postgres for the service to persist the information about the created instances
and where do we get one? Yes, we create a docker postgres instance just like all other instances.

First we need a config file where we set the credentials for the meta database and this need to be called
`postgraas_server.cfg` and must be located in the CWD::

    [metadb]
    db_name = postgraas
    db_username = postgraas
    db_pwd = very_secure_postgraas
    host = localhost
    port = 5432

For the creation of the meta db container and creation of the schema, there is a convenience entry point::

    postgraas_init

With this, everything is prepared and we can start the postgraas server, for example with gunicorn::

    gunicorn -w 4 -b 0.0.0.0:8080 postgraas_server.postgraas_api:app

This will start the server, listening on port 8080 and all incoming interfaces (DISCLAIMER: please don't use anything
like this in a production like environment)

Ready to serve your postgres instances!

PostgreSQL Cluster
==================

In case you don't want to use Docker and just use a plain Postgres cluster instance,
you have to add another section to your config to change the default backend::

    [backend]
    type = pg_cluster
    host = localhost
    port = 5432
    database = postgres
    username = postgres
    password = S3cr3t

The given user has to be able to create new ``roles`` and ``databases`` on the specified
cluster.

In case you need to log in with usernames of the form ``<username@hostname>``,
you can use the optional ``server`` config option::

    [backend]
    type = pg_cluster
    host = localhost
    port = 5432
    database = postgres
    username = postgres
    password = S3cr3t
    server = postgraas-instance-1

.. note::

    A big difference to the Docker backend is that with the ``pg_cluster`` backend
    users only get single database, while for the docker backend they get a whole
    Postgres instance.
