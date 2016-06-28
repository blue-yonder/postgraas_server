"""
config

:file: configuration.py
:date: 18.08.2014
:authors: nohnezat
"""
import os
import logging
import ConfigParser

__all__ = ['get_config', 'get_config_filename', 'expand_env_vars']

logger = logging.getLogger(__name__)


def get_global_config_path():
    return os.path.abspath(os.getcwd())


def get_config_filename():
    config_filename = os.path.join(get_global_config_path(), "postgraas_server.cfg")
    return config_filename


def get_config(config_filename=None):
    config = ConfigParser.RawConfigParser()
    if not config_filename:
        config_filename = get_config_filename()
    logger.debug('config filename: {}'.format(config_filename))
    config.read(config_filename)
    expand_env_vars(config)
    return config


def expand_env_vars(config):
    for sec in config.sections():
        for opt in config.options(sec):
            config.set(sec, opt, os.path.expandvars(config.get(sec, opt)))


def config_logging():
    file_name = os.path.join(get_global_config_path(), "logging.conf")
    if os.path.exists(file_name):
        logging.config.fileConfig(file_name, disable_existing_loggers=False)
    else:
        logging.basicConfig(level=logging.DEBUG)
        logger.warning('logging config file does not exist {}'.format(file_name))


def get_meta_db_config_path(config):
    DB_PATH = 'postgresql://{db_username}:{db_pwd}@{host}:{port}/{db_name}'.format(
        db_name=config.get('metadb', 'db_name'),
        db_username=config.get('metadb', 'db_username'),
        db_pwd=config.get('metadb', 'db_pwd'),
        host=config.get('metadb', 'host'),
        port=config.get('metadb', 'port')
    )
    return DB_PATH
