import json
from jsonschema import validate, ValidationError, draft7_format_checker
from flask import Response, current_app, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import UnsupportedMediaType, NotFound, Conflict, BadRequest
from sensorhub.models import Stats
from sensorhub import db
from sensorhub.utils import get_rabbit_connection
from sensorhub.constants import *


class SensorStats(Resource):

    def get(self, sensor):
        if sensor.stats:
            body = sensor.stats.serialize()
            return Response(json.dumps(body), 200, mimetype=JSON)
        else:
            self._send_task(sensor)
            return Response(status=202)

    def put(self, sensor):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(
                request.json,
                Stats.json_schema(),
                format_checker=draft7_format_checker
            )
        except ValidationError as e:
            print(e)
            raise BadRequest(description=str(e))

        stats = Stats()
        stats.deserialize(request.json)
        sensor.stats = stats
        db.session.add(sensor)
        db.session.commit()
        return Response(status=204)

    def delete(self, sensor):
        db.session.delete(sensor.stats)
        db.session.commit()
        return Response(status=204)

    def _send_task(self, sensor):
        # get sensor measurements, values only
        body = {
            "data": [meas.value for meas in sensor.measurements],
            "sensor": sensor.name
        }

        # form a connection, open channel and declare a queue
        connection = get_rabbit_connection()
        channel = connection.channel()
        channel.queue_declare(queue="stats")

        # publish message (task) to the default exchange
        channel.basic_publish(
            exchange="",
            routing_key="stats",
            body=json.dumps(body)
        )
        connection.close()
