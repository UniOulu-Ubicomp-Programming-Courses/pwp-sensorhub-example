import json
from datetime import datetime
from flask import Flask, Response, abort, request
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine
from sqlalchemy import event
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
api = Api(app)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

deployments = db.Table("deployments",
    db.Column("deployment_id", db.Integer, db.ForeignKey("deployment.id"), primary_key=True),
    db.Column("sensor_id", db.Integer, db.ForeignKey("sensor.id"), primary_key=True)
)



class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    altitude = db.Column(db.Float, nullable=True)
    description=db.Column(db.String(256), nullable=True)

    sensor = db.relationship("Sensor", back_populates="location", uselist=False)


class Deployment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    name = db.Column(db.String(128), nullable=False)

    sensors = db.relationship("Sensor", secondary=deployments, back_populates="deployments")


class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    model = db.Column(db.String(128), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id"), unique=True)

    location = db.relationship("Location", back_populates="sensor")
    measurements = db.relationship("Measurement", back_populates="sensor")
    deployments = db.relationship("Deployment", secondary=deployments, back_populates="sensors")


class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey("sensor.id", ondelete="SET NULL"))
    value = db.Column(db.Float, nullable=False)
    time = db.Column(db.DateTime, nullable=False)

    sensor = db.relationship("Sensor", back_populates="measurements")


class SensorConverter(BaseConverter):

    def to_python(self, sensor_name):
        db_sensor = Sensor.query.filter_by(name=sensor_name).first()
        if db_sensor is None:
            raise NotFound
        return db_sensor

    def to_url(self, db_sensor):
        return db_sensor.name


class SensorCollection(Resource):

    def get(self):
        response_data = []
        sensors = Sensor.query.all()
        for sensor in sensors:
            response_data.append([sensor.name, sensor.model])
        return response_data

    def post(self):
        if not request.json:
            abort(415)

        try:
            sensor = Sensor(
                name=request.json["name"],
                model=request.json["model"],
            )
            db.session.add(sensor)
            db.session.commit()
        except KeyError:
            abort(400)
        except IntegrityError:
            abort(409)

        return Response(status=201, headers={
            "Location": api.url_for(SensorItem, sensor=sensor)
        })


class SensorItem(Resource):

    def get(self, sensor):
        return {
            "name": sensor.name,
            "model": sensor.model,
            "location": sensor.location and sensor.location.name
        }

    def put(self, sensor):
        pass

    def delete(self, sensor):
        db.session.delete(sensor)
        db.session.commit()

        return Response(status=204)


app.url_map.converters["sensor"] = SensorConverter

api.add_resource(SensorCollection, "/api/sensors/")
api.add_resource(SensorItem, "/api/sensors/<sensor:sensor>/")
