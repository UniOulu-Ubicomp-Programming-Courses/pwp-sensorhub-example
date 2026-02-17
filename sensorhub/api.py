from flask import Blueprint
from flask_restful import Api

from .resources.sensor import SensorCollection, SensorItem
from .resources.measurement import MeasurementCollection
from . import views

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api_bp.add_url_rule("/", "entry", views.entry)
api.add_resource(SensorCollection, "/sensors/")
api.add_resource(SensorItem, "/sensors/<sensor:sensor>/")
api.add_resource(MeasurementCollection, "/sensors/<sensor:sensor>/measurements/")
