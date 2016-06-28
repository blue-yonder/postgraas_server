import logging
from create_app import create_app
from configuration import get_config

logger = logging.getLogger(__name__)


app = create_app(get_config())


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
