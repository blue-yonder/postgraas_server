import ConfigParser

from .docker import DockerBackend
from .postgres_cluster import PGClusterBackend

BACKENDS = {'docker': DockerBackend, 'pg_cluster': PGClusterBackend}


def get_backend(config):
    backend_config = {}
    try:
        backend_config = dict(config.items('backend'))
        backend = backend_config['type']
    except ConfigParser.NoSectionError:
        backend = 'docker'
    return BACKENDS[backend](backend_config)
