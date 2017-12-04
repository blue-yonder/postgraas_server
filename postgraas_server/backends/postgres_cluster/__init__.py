from . import postgres_cluster_driver as pgcd
from ..exceptions import PostgraasApiException


class PGClusterBackend(object):
    def __init__(self, config):
        self.config = config

    def create(self, entity, connection_info):
        try:
            pgcd.create_postgres_db(connection_info, self.config)
        except ValueError as e:
            raise PostgraasApiException(str(e))
        return None

    def delete(self, entity):
        try:
            pgcd.delete_database(entity.db_name, self.config)
            pgcd.delete_user(entity.username, self.config)
        except ValueError as e:
            if 'does not exist' in e.args[0]:
                raise PostgraasApiException("Could not delete, does not exist {}".format(entity.db_name))
            else:
                raise PostgraasApiException(str(e))

    def exists(self, entity):
        return pgcd.check_db_or_user_exists(entity.db_name, entity.username, self.config)

    @property
    def hostname(self):
        return self.config['host']

    @property
    def port(self):
        return self.config['port']

    @property
    def server(self):
        return self.config['server']

    @property
    def master_hostname(self):
        return self.hostname
