import logging

from sqlalchemy import inspect
from sqlalchemy.ext.declarative.clsregistry import _ModuleMarker
from sqlalchemy.orm import RelationshipProperty

logger = logging.getLogger(__name__)


def is_sane_database(Base, session):  # pragma: no cover
    """
    from: http://stackoverflow.com/questions/30428639/check-database-schema-matches-sqlalchemy-models-on-application-startup
    Check whether the current database matches the models declared in model base.

    Currently we check that all tables exist with all columns. What is not checked

    * Column types are not verified

    * Relationships are not verified at all (TODO)

    :param Base: Declarative Base for SQLAlchemy models to check

    :param session: SQLAlchemy session bound to an engine

    :return: True if all declared models have corresponding tables and columns.
    """
    engine = session.get_bind()
    iengine = inspect(engine)
    errors = False
    tables = iengine.get_table_names()

    # Go through all SQLAlchemy models
    for name, klass in Base._decl_class_registry.items():
        if isinstance(klass, _ModuleMarker):
            # Not a model
            continue
        table = klass.__tablename__
        if table in tables:
            # Check all columns are found
            # Looks like [{'default': "nextval('sanity_check_test_id_seq'::regclass)", 'autoincrement': True, 'nullable': False, 'type': INTEGER(), 'name': 'id'}]
            columns = [c["name"] for c in iengine.get_columns(table)]
            mapper = inspect(klass)
            for column_prop in mapper.attrs:
                if isinstance(column_prop, RelationshipProperty):
                    # TODO: Add sanity checks for relations
                    pass
                else:
                    for column in column_prop.columns:
                        # Assume normal flat column
                        if column.key not in columns:
                            logger.error(
                                "Model %s declares column %s which does not exist in database %s",
                                klass, column.key, engine
                            )
                            errors = True
        else:
            logger.error(
                "Model %s declares table %s which does not exist in database %s", klass, table,
                engine
            )
            errors = True
    return not errors


def init_db(postgraas_app):
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()

    from postgraas_server.management_resources import db
    with postgraas_app.app_context():
        if not is_sane_database(db.Model, db.session):
            db.drop_all()
            db.create_all()
