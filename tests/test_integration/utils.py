import time

from postgraas_server.backends.docker.postgres_instance_driver import _docker_client


def wait_for_postgres_listening(container_id, timeout=10):
    """
    Inspect/follow the output of the docker container logs until encountering the
    message from postgres that it accepts connections.

    Raises in case the container does not exist.

    Caveat: this check is specific to the used docker image.
    Tested for current postgres:9.4 image.

    :returns: boolean, whether the message has been (True), or the timeout has been hit (False).
    """
    c = _docker_client()
    cont = c.containers.get(container_id)
    for i in range(max(int(timeout * 10), 1)):
        # not very efficient to always gather all logs, but as we only use it for testing
        # and it seems to be fast enough, should be OK.
        output = cont.logs(stdout=True, stderr=True)
        # the startup script in the docker image starts postgres twice,
        # so wait for the second start:
        if output.count(b'database system is ready to accept connections') >= 2:
            return True
        time.sleep(0.1)
    return False
