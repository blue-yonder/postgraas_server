=====
Usage
=====

Intentionally the usage is a simple stupid REST'ish api, in fact there is only `create` a new instance, `delete`
an existing instance, list all instances and `read/get` the details of an instance.

Create a postgraas Instance
===========================

We need to send all the required parameters for the creation as an http request. This is quite convenient
by creating a file e.g. `my_postgraas.json`::

    {
        "postgraas_instance_name": "my_postgraas",
        "db_name": "my_db",
        "db_username": "db_user",
        "db_pwd": "secret"
    }

and making a POST request to the collection resource with `curl`::

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

Awesome, isn't it?

List all instances
==================

With a GET request to the collection resource you get a list of all instances (not only the one you created...)::

    curl -H "Content-Type: application/json" -X GET http://localhost:8080/api/v2/postgraas_instances

And the response is the list::

    [
        {
            "username": "db_user",
            "container_id": "193f0d94d49fa26626fdbdb583e9453f923468b01eac59207b4852831a105c03",
            "db_name": "my_db",
            "postgraas_instance_name": "my_postgraas",
            "password": "",
            "creation_timestamp": "2016-07-06T23:38:38.367493",
            "id": 1,
            "hostname": "not imlemented yet",
            "port": "54648"
        }
    ]


Delete an instance
==================

With a DELETE request to the uri of the instance you can delete an instance::

    curl -H "Content-Type: application/json" -X DELETE --data @pwd.json http://localhost:8080/api/v2/postgraas_instances/1

where the `pwd.json` file contains the postgres password as "db_pwd" key, e.g.::

    {
        "db_pwd": "secret"
    }


You will get a response like this::

    {
        "status": "success",
        "msg": "deleted postgraas instance"
    }

That's it at the moment!