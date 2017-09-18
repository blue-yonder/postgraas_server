=============
Configuration
=============

Besides the already seen backend config options, it is also possible to
configure the application itself.
You can for example change the behaviour of `sqlalchemy`_ or integrate `sentry`_::

    [application]
    SQLALCHEMY_POOL_RECYCLE = 120
    SQLALCHEMY_POOL_SIZE = 1
    SENTRY_DSN = https://<key>:<secret>@sentry.io/<project>
    SENTRY_ENVIRONMENT = production

.. _sqlalchemy: http://flask-sqlalchemy.pocoo.org/2.2/config/
.. _sentry: https://docs.sentry.io