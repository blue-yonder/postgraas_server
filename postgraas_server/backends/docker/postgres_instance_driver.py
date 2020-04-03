import docker


def get_hostname():
    # mmmh, how should this be done? need nome kind ouf routing...
    return 'not implemented yet'


def _docker_client():
    return docker.DockerClient(base_url='unix://var/run/docker.sock', version='auto', timeout=30)


def get_open_port():
    # this should be done somewhere else, e.g docker itself, but for now...
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


def get_container_by_name(postgraas_instance_name):
    # return the container object or None if not found
    c = _docker_client()
    try:
        return c.containers.get(postgraas_instance_name)
    except docker.errors.NotFound:
        return None


def check_container_exists(postgraas_instance_name):
    if get_container_by_name(postgraas_instance_name):
        return True
    return False


def create_postgres_instance(postgraas_instance_name, connection_dict):
    c = _docker_client()
    environment = {
        "POSTGRES_USER": connection_dict['db_username'],
        "POSTGRES_PASSWORD": connection_dict['db_pwd'],
        "POSTGRES_DB": connection_dict['db_name']
    }
    internal_port = 5432
    if check_container_exists(postgraas_instance_name):
        raise ValueError('Container exists already')
    image = 'postgres:9.4'
    container = c.containers.create(
        image,
        name=postgraas_instance_name,
        ports={internal_port: connection_dict['port']},
        environment=environment,
        restart_policy={"Name": "unless-stopped"},
        labels={"postgraas": image}
    )
    container.start()
    return container.id


def delete_postgres_instance(container_id):
    c = _docker_client()
    c.containers.get(container_id).remove(force=True)
