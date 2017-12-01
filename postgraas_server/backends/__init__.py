from .docker import DockerBackend
from .postgres_cluster import PGClusterBackend

BACKENDS = {'docker': DockerBackend, 'pg_cluster': PGClusterBackend}


def get_backend(config):
    backend_config = {}
    try:
        backend_config = config['backend']
        backend = backend_config['type']
    except KeyError:
        backend = 'docker'
    return BACKENDS[backend](backend_config)
