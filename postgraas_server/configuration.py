import os
import logging
import ConfigParser

__all__ = ['get_config', 'get_config_filename', 'expand_env_vars']

logger = logging.getLogger(__name__)


def get_default_config_filename():
    config_filename = os.path.join(os.path.abspath(os.getcwd()), "postgraas_server.cfg")
    return config_filename


def get_config(config_filename=get_default_config_filename()):
    config = ConfigParser.RawConfigParser()
    logger.debug('config filename: {}'.format(config_filename))
    config.read(config_filename)
    expand_env_vars(config)
    return config


def expand_env_vars(config):
    for sec in config.sections():
        for opt in config.options(sec):
            config.set(sec, opt, os.path.expandvars(config.get(sec, opt)))


def get_meta_db_config_path(config):
    db_path = 'postgresql://{db_username}:{db_pwd}@{host}:{port}/{db_name}'.format(
        db_name=config.get('metadb', 'db_name'),
        db_username=config.get('metadb', 'db_username'),
        db_pwd=config.get('metadb', 'db_pwd'),
        host=config.get('metadb', 'host'),
        port=config.get('metadb', 'port')
    )
    return db_path
