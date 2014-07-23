__author__ = 'neubauer'

from flask import Flask, request, jsonify
import docker
import hashlib
import socket
app = Flask(__name__)

def get_unique_id(connection_dict):
    return hashlib.sha1(str(frozenset(connection_dict.items()))).hexdigest()

def get_open_port():
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("",0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port

def create_postgres_instance(connection_dict):
    #docker run -d -p 5432:5432 -e POSTGRESQL_USER=test -e POSTGRESQL_PASS=oe9jaacZLbR9pN -e POSTGRESQL_DB=test orchardup/postgresql
    c = docker.Client(base_url='unix://var/run/docker.sock',
                  version='1.12',
                  timeout=10)
    environment = {
        "POSTGRESQL_USER": connection_dict['db_username'],
        "POSTGRESQL_PASS": connection_dict['db_pwd'],
        "POSTGRESQL_DB": connection_dict['db_name']
    }
    internal_port = 5432
    container_info = c.create_container('orchardup/postgresql', ports=[internal_port], environment=environment)
    container_id = container_info['Id']
    port_dict = {internal_port: connection_dict['port']}
    c.start(container_id, port_bindings=port_dict)
    return container_id

def get_hostname():
    #return socket.gethostbyname(socket.gethostname())
    return "XXX.XXX.XXX.XXX"


@app.route("/postgraas/one_db_please")
def hello():
    db_credentials = {
    "db_name": request.args.get('db_name', ''),
    "db_username": request.args.get('db_username', ''),
    "db_pwd": request.args.get('db_pwd', ''),
    "host": get_hostname(),
    "port": get_open_port()
    }
    db_credentials['db_id'] = get_unique_id(db_credentials)
    db_credentials['container_id'] = create_postgres_instance(db_credentials)
    return jsonify(db_credentials)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
