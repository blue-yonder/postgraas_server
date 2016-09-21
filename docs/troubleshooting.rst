===============
Troubleshooting
===============

Errors while installing the requirements
========================================

**'Error: pg_config executable not found.'**

You need to install the dev version of `libpq <https://www.postgresql.org/docs/9.1/static/libpq.html>`_.
On Debian Jessie for example, you can do this with::

    apt-get install libpq-dev

**'./psycopg/psycopg.h:30:20: fatal error: Python.h: No such file or directory'**

You need to install the dev version of Python.
On Debian Jessie for example, you can do this with::

    apt-get install python-dev
