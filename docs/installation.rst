============
Installation
============

Prequisites
===========

* Tested on Debian/Ubuntu
* Python tested with 2.7
* Docker Engine >= 1.6.0
* Any wsgi server, tested with gunicorn
* recent pip & setuptools

Install via pip::

    pip install postgraas_server

Pull the official postgres docker `image <https://hub.docker.com/_/postgres/>`_::

    docker pull postgres

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

Ready to serve you postgres instances!

