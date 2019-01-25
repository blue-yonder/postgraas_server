import errno
import json
import logging

import os

__all__ = ['get_config', 'get_default_config_filename', 'get_application_config', 'expand_env_vars']

logger = logging.getLogger(__name__)


def get_default_config_filename():
    config_filename = os.path.join(os.path.abspath(os.getcwd()), "application.cfg")
    return config_filename


def _load_secrets(filename='/secrets'): # pragma: no cover
    try:
        with open(filename, 'r') as secrets_file:
            secrets = json.load(secrets_file)
    except IOError as e:
        if e.errno in (errno.ENOENT, errno.EISDIR):
            return {}
        e.strerror = 'Unable to load configuration file (%s)' % e.strerror
        raise
    return secrets


def get_config(config_filename=None, secrets_file='/secrets'):
    config_filename = config_filename or get_default_config_filename()
    logger.debug('config filename: {}'.format(config_filename))
    with open(config_filename, 'r') as cfg:
        config = json.load(cfg)
    secrets = _load_secrets(filename=secrets_file)
    if secrets: # pragma: no cover
        try:
            import secure_config.secrets as sec
            config = sec.load_secret_dict(password=secrets['encryption_key'], config_dict=config)
        except ImportError as e:
            logger.debug('secure_config not installed')

    return config


def get_application_config(config):
    try:
        return config['application']
    except KeyError:
        return []


def get_meta_db_config_path(config):
    username = get_user(config)
    password = get_password(config)
    db_path = 'postgresql://{db_username}:{db_pwd}@{host}:{port}/{db_name}'.format(
        db_name=config['metadb']['db_name'],
        db_username=username,
        db_pwd=password,
        host=config['metadb']['host'],
        port=config['metadb']['port']
    )
    return db_path


def get_user(config):
    try:
        server = config['metadb']['server']
        username = '@'.join([config['metadb']['db_username'], server])
    except KeyError:
        username = config['metadb']['db_username']
    return username


def get_password(config):
    try:
        password = config['metadb']['db_pwd'].decrypt()
    except AttributeError:
        password = config['metadb']['db_pwd']
    return password
