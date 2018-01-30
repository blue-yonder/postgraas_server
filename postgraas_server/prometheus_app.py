#!/usr/bin/env python
# coding=utf-8

import logging
from contextlib import contextmanager

import click
import psycopg2
from flask import Blueprint, Flask, Response, abort
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from prometheus_client.core import REGISTRY, GaugeMetricFamily

import postgraas_server.configuration as cfg

logger = logging.getLogger(__name__)

_NO_TRACING = 0


@contextmanager
def db_connection(config):
    username = cfg.get_user(config)
    with psycopg2.connect(
        database=config['metadb']['db_name'],
        user=username,
        password=config['metadb']['db_pwd'],
        host=config['metadb']['host'],
        port=config['metadb']['port']
    ) as connection:
        yield connection


def do_count_query(config):
    with db_connection(config) as conn:
        with conn.cursor() as cursor:
            sql = (
                "SELECT count(*) FROM pg_database "
                "WHERE datistemplate = false;"
            )
            cursor.execute(sql)
            (count,) = cursor.fetchone()

    return count


def count_postgraas_instances(config):
    count = do_count_query(config)
    return count


class CustomCollector(object):
    def __init__(self, config):
        self.metric_name = 'number_of_postgraas_instances'
        self.help = 'number of postgraas instances'
        self.config = config

    def collect(self):
        count = count_postgraas_instances(self.config)
        count_metric = GaugeMetricFamily(self.metric_name, self.help, value=count)
        yield count_metric

    def describe(self):
        yield GaugeMetricFamily(self.metric_name, self.help)


blueprint = Blueprint('monitoring', __name__)


@blueprint.route('/health')
def health():
    return 'ok'


@blueprint.route('/')
@blueprint.route('/metrics')
def metrics():
    try:
        content = generate_latest(REGISTRY)
        return content, 200, {'Content-Type': CONTENT_TYPE_LATEST}
    except Exception as error:
        logging.exception("Any exception occured during scraping")
        abort(Response("Scrape failed: {}".format(error), status=502))


@click.command()
@click.option("--test", is_flag=True, help="Print the results of a single readout instead of running a web server")
@click.option("--port", default=8000, help="Set the port for running the web server that is scraped by prometheus")
def run_server(test, port):
    """
    This script provides monitoring information about the postgraas server.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s")

    config = cfg.get_config()

    collector = CustomCollector(config)
    if test:
        click.echo("TEST MODE")
        for metric in collector.collect():
            for sample in metric.samples:
                click.echo(sample)
    else:
        click.echo("Running web server at port {}".format(port))
        REGISTRY.register(collector)
        app = Flask(__name__)
        app.register_blueprint(blueprint)
        app.run(host='0.0.0.0', port=port, threaded=True)


if __name__ == '__main__':
    run_server()
