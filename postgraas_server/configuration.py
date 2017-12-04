import errno
import json
import logging
from configparser import ConfigParser

import os

__all__ = ['get_config', 'get_default_config_filename', 'get_application_config', 'expand_env_vars']

logger = logging.getLogger(__name__)


def get_default_config_filename():
    config_filename = os.path.join(os.path.abspath(os.getcwd()), "application.cfg")
    return config_filename


def _load_secrets(filename='/secrets'):
    try:
        with open(filename, 'r') as secrets_file:
            secrets = json.loads(secrets_file.read())
            print(secrets)
    except IOError as e:
        if e.errno in (errno.ENOENT, errno.EISDIR):
            return {}
        e.strerror = 'Unable to load configuration file (%s)' % e.strerror
        raise
    return secrets


def get_config(config_filename=get_default_config_filename(), secrets_file='/secrets'):
    config = ConfigParser()
    logger.debug('config filename: {}'.format(config_filename))
    secrets = _load_secrets(filename=secrets_file)
    if secrets:
        from cryptography.fernet import Fernet
        f = Fernet(secrets['encryption_key'].encode())
        with open(config_filename, 'rb') as cfg:
            cfg_content = f.decrypt(cfg.read())
        print(cfg_content)
        config.read_string(cfg_content.decode("utf-8"))
    else:
        config.read(config_filename)
    expand_env_vars(config)
    return config


def expand_env_vars(config):
    for sec in config.sections():
        for opt in config.options(sec):
            config.set(sec, opt, os.path.expandvars(config.get(sec, opt)))


def get_application_config(config):
    try:
        return config['application']
    except KeyError:
        return []


def get_meta_db_config_path(config):
    username = get_user(config)

    db_path = 'postgresql://{db_username}:{db_pwd}@{host}:{port}/{db_name}'.format(
        db_name=config.get('metadb', 'db_name'),
        db_username=username,
        db_pwd=config.get('metadb', 'db_pwd'),
        host=config.get('metadb', 'host'),
        port=config.get('metadb', 'port')
    )
    return db_path


def get_user(config):
    server = config.get('metadb', 'server', fallback=None)
    if server:
        username = '@'.join([config.get('metadb', 'db_username'), server])
    else:
        username = config.get('metadb', 'db_username')
    return username
