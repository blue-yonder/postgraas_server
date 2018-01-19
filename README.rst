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

Postgraas offers `CRUD <https://de.wikipedia.org/wiki/CRUD>`_ operations for complete PostgreSQL database instances via a simple REST api. The database instances are docker containers and the api server is a few hundred LoC Flask application. It is of not meant as a production ready solution, but more a proof-of-concept to spread the idea of creating "as-a-service" services easily yourself and should inspire you to start working on your own cloud infrastructure today. But in fact, it proofs the concept very well and it turned out to be super useful for delivering a PostgreSQL instance if you need one fast: for integration tests, for playing around with fancy ShowHN projects or other experiments. The CRUD management via REST api is of course also a necessary prequisite for building an automated continuous delivery pipeline for a modern software project. 

Installation
============
You can find detailed instructions in the `docs <http://postgraas-server.readthedocs.io/en/latest/installation.html>`_

Install via pip::

    pip install postgraas_server
    
And start the wsgi api server for example with gunicorn::

    gunicorn -w 4 -b 0.0.0.0:8080 postgraas_server.postgraas_api:app
    

Usage
=====

We need to send all the required parameters for the creation as an http request. This is quite convenient by creating a file e.g. ``my_postgraas.json``::

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
         "host": "not imlemented yet",
         "db_name": "my_db",
         "db_username": "db_user",
         "port": 54648
    }

We are now able to connect to the database for exaple with psql::

    psql -h localhost -p 54648 -U db_user my_db

Awesome, isn’t it?

Development
===========

Run the tests
-------------

You need to have docker installed

Make sure you pull the right docker image::

    docker pull postgres:9.4

Make a virtualenv and install the requirements including the dev requirements and a local editable intsall
of the package, for convenience you can install the requirements.in ::

    pip install -r requirements.in
    pip install -r requirements_dev.txt

For the tests you need a running postgres meta database and set some enviroonment variables accordingly.
There is a convenience script to set this all up using a docker postgres database::

    . setup_integration_test_docker.sh

Now you should be able to execute the tests::

    py.test tests/
