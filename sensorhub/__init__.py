import os
from flasgger import Swagger
from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
cache = Cache()

# Based on http://flask.pocoo.org/docs/1.0/tutorial/factory/#the-application-factory
# Modified to use Flask SQLAlchemy
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CACHE_TYPE="FileSystemCache",
        CACHE_DIR=os.path.join(app.instance_path, "cache"),
        SWAGGER = {
            "title": "Sensorhub API",
            "openapi": "3.0.4",
            "uiversion": 3,
            "doc_dir": "sensorhub/doc",
        },
        RABBITMQ_BROKER_ADDR="amqp://localhost/",
        RABBIT_USE_TLS=False,
    )

    swagger = Swagger(app, template_file="doc/base.yml")

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    cache.init_app(app)

    from . import models
    from . import api
    from .utils import SensorConverter
    app.cli.add_command(models.init_db_command)
    app.cli.add_command(models.generate_test_data)
    app.cli.add_command(models.generate_master_key)
    app.url_map.converters["sensor"] = SensorConverter
    app.register_blueprint(api.api_bp)

    return app
