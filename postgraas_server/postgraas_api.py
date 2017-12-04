import logging

from postgraas_server.configuration import get_config
from postgraas_server.create_app import create_app

logger = logging.getLogger(__name__)

app = create_app(get_config())

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
