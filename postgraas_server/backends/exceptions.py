class PostgraasApiException(Exception):
    """Base exception which should be used by backends instead of their own
    backend specific exceptions.

    .. example::

        try:
            docker_backend.do_something()
        except docker.errors.APIError as e:
            raise PostgraasApiException(str(e))

    """

    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message
