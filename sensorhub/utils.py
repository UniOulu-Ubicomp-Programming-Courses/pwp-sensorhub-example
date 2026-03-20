from functools import wraps
import json
import secrets
import ssl
from flask import current_app, request
import pika
from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.routing import BaseConverter

from .models import ApiKey, Sensor

class SensorConverter(BaseConverter):

    def to_python(self, sensor_name):
        db_sensor = Sensor.query.filter_by(name=sensor_name).first()
        if db_sensor is None:
            raise NotFound
        return db_sensor

    def to_url(self, db_sensor):
        return db_sensor.name


def page_key(*args, **kwargs):
    page = request.args.get("page", 0)
    return request.path + f"[page_{page}]"

def require_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key_hash = ApiKey.key_hash(request.headers.get("Sensorhub-Api-Key", "").strip())
        db_key = ApiKey.query.filter_by(admin=True).first()
        if secrets.compare_digest(key_hash, db_key.key):
            return func(*args, **kwargs)
        raise Forbidden
    return wrapper

def require_sensor_key(func):
    @wraps(func)
    def wrapper(self, sensor, *args, **kwargs):
        key_hash = ApiKey.key_hash(request.headers.get("Sensorhub-Api-Key").strip())
        db_key = ApiKey.query.filter_by(sensor=sensor).first()
        if db_key is not None and secrets.compare_digest(key_hash, db_key.key):
            return func(*args, **kwargs)
        raise Forbidden
    return wrapper

def get_rabbit_connection():
    if current_app.config["RABBITMQ_USE_TLS"]:
        context = ssl.create_default_context(cafile=current_app.config["CA_CERT"])
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_cert_chain(
            current_app.config["CLIENT_CERT"],
            current_app.config["CLIENT_KEY"],
        )
        ssl_options = pika.SSLOptions(context)
        credentials = pika.PlainCredentials(
            current_app.config["RABBITMQ_USER"], current_app.config["RABBITMQ_PASS"]
        )
        conn_params = pika.ConnectionParameters(
            current_app.config["RABBITMQ_HOST"],
            current_app.config["RABBITMQ_PORT"],
            current_app.config["RABBITMQ_VHOST"],
            credentials,
            ssl_options=ssl_options
        )
    else:
        conn_params = pika.ConnectionParameters(
            current_app.config["RABBITMQ_HOST"],
            current_app.config["RABBITMQ_PORT"],
            current_app.config["RABBITMQ_VHOST"],
        )
    return pika.BlockingConnection(conn_params)
