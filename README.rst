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

Postgraas offers `CRUD <https://de.wikipedia.org/wiki/CRUD>`_ operations for complete PostgreSQL database instances via a simple REST api. The database instances are docker containers and the api server is a few hundred LoC Flask application. It is of not meant as a production ready solution, but more a proof-of-concept to spread the idea of creating "as-a-service" services easily yourself and should inspire you to start working on your own cloud infrastructure today. But in fact, it proofs the concept very well and it turned out to be super useful for delivering a PostgreSQL instance if you need one fast: for integration tests, for playing around with fancy ShowHN projects or other experiments. The CRUD operations via REST api is of course also a necessary prequisite for building an automated continuous delivery pipeline for your quality project. 



Usage
=====




