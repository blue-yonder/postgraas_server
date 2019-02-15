from postgraas_server.backends import get_backend
from postgraas_server.backends.docker import DockerBackend
from postgraas_server.backends.postgres_cluster import PGClusterBackend


def test_get_backend_docker():
    config = {"backend": {
        "type": "docker"
        }
    }
    backend_config = get_backend(config)
    assert isinstance(backend_config, DockerBackend)


def test_get_backend_pg_cluster():
    config = {"backend": {
        "type": "pg_cluster"
        }
    }
    backend_config = get_backend(config)
    assert isinstance(backend_config, PGClusterBackend)


def test_get_backend_docker_default():
    config = {}
    backend_config = get_backend(config)
    assert isinstance(backend_config, DockerBackend)
