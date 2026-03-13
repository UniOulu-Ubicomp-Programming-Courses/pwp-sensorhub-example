from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, UnsupportedMediaType

from sensorhub import db
from sensorhub.models import Sensor
from sensorhub.utils import require_admin


class SensorCollection(Resource):

    @require_admin
    def get(self):
        response_data = []
        sensors = Sensor.query.all()
        for sensor in sensors:
            response_data.append(sensor.serialize())
        return response_data

    @require_admin
    def post(self):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Sensor.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        sensor = Sensor()
        sensor.deserialize(request.json)
        try:
            db.session.add(sensor)
            db.session.commit()
        except KeyError as e:
            raise BadRequest(description=str(e))
        except IntegrityError:
            raise Conflict(
                description="Sensor with name '{name}' already exists.".format(
                    **request.json
                )
            )

        return Response(status=201, headers={
            "Location": url_for("api.sensoritem", sensor=sensor)
        })


class SensorItem(Resource):

    def get(self, sensor):
        return sensor.serialize()

    @require_admin
    def put(self, sensor):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Sensor.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        sensor.deserialize(request.json)
        try:
            db.session.add(sensor)
            db.session.commit()
        except IntegrityError:
            raise Conflict(
                description="Sensor with name '{name}' already exists.".format(
                    **request.json
                )
            )

        return Response(status=204)

    def delete(self, sensor):
        pass
