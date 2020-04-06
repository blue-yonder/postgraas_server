=========
Changelog
=========

v2.1.4
======

- Fixed some errors in README.rst that prevented successfull build

v2.1.3
======

- Prevent internal server errors upon database delete when there are multiple active sessions

v2.1.2
======

- Blacklist postgres as username

v2.1.1
======

- Allow user to supply username in the format `user@host` himself.

v2.1.0
======

- init-db now constructs usernames identical to the server. Thus, `user@host` names now work properly.
- Fix log messages of Gunicorn and Flask not ending up in the root logger.`

v2.0.2
======

- return proper HTTP status codes, when deleting postgraas instances

v2.0.1
======

- prevent creation of databases with an empty password as those cannot be removed.
- return http status code 409 instead of 200 in case of a name conflict during creation of a new
  instance.

v2.0.0
======

- security: Harden the Postgres cluster backend against SQL injections.
- hardened the server against leaking of database connections and transactions.

v2.0.0b1
========

- breaking change: config not ini anymore, but json
- add support for secure-config (experimental)

v1.0.0b3
========

- add support for simple Postgres Cluster as backend
- add support for sentry (https://sentry.io)
- bugfix: varchar(50) field in the DB too small for hostname

v0.1.9
======

- added authentication to delete resource

v0.1.8
======

- added init script
- fixed postgraas to 9.4

v0.1.7
======

- fixed docker version 1.12

v0.1.6
======

- bugfix: password was not set in instance

v0.1.5
======

- automated release process via travis
- fixed meta db initialization

v0.1.4
======

- removed postgraas instance one and fixed the tests

v0.1.3
======

- Introduced completely new API v2

v0.1.0
======

- First running version


