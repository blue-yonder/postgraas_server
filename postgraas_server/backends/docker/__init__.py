# from . import postgres_instance_driver as pg
from ..exceptions import PostgraasApiException


class DockerBackend(object):
    def __init__(self, config=None):
        self.config = config

    def create(self, entity, connection_info):
        from docker.errors import APIError
        from . import postgres_instance_driver as pg
        try:
            return pg.create_postgres_instance(entity.postgraas_instance_name, connection_info)
        except (APIError, ValueError) as e:
            raise PostgraasApiException(str(e))

    def delete(self, entity):
        from docker.errors import APIError, NullResource, NotFound
        from . import postgres_instance_driver as pg
        if not entity.container_id:
            raise PostgraasApiException("container ID not provided")
        try:
            return pg.delete_postgres_instance(entity.container_id)
        except NotFound as e:
            raise PostgraasApiException("Could not delete, does not exist {}".format(entity.container_id))
        except (APIError, NullResource) as e:
            raise PostgraasApiException(str(e))

    def exists(self, entity):
        from . import postgres_instance_driver as pg
        if entity.postgraas_instance_name:
            return pg.check_container_exists(entity.postgraas_instance_name)
        else:
            False

    @property
    def hostname(self):
        from . import postgres_instance_driver as pg
        return pg.get_hostname()

    @property
    def port(self):
        from . import postgres_instance_driver as pg
        return pg.get_open_port()

    @property
    def master_hostname(self):
        return '127.0.0.1'
