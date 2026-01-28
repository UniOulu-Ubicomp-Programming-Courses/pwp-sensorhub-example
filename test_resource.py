import datetime
import json
import os
import random
import pytest

from app import Measurement, Sensor, app, db



@pytest.fixture
def client():
    ctx = app.app_context()
    ctx.push()

    db.create_all()
    _populate_db()

    yield app.test_client()

    db.session.rollback()
    db.drop_all()
    db.session.remove()
    ctx.pop()

def _populate_db():
    for i in range(1, 4):
        s = Sensor(
            name="test-sensor-{}".format(i),
            model="testsensor"
        )

        now = datetime.datetime.now()
        interval = datetime.timedelta(seconds=10)
        for i in range(125):
            meas = Measurement(
                value=round(random.random() * 100, 2),
                time=now
            )
            now += interval
            s.measurements.append(meas)

        db.session.add(s)

    db.session.commit()

def _get_sensor_json(number=1):
    """
    Creates a valid sensor JSON object to be used for PUT and POST tests.
    """

    return {"name": "extra-sensor-{}".format(number), "model": "extrasensor"}


class TestSensorCollection:

    RESOURCE_URL = "/api/sensors/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body) == 3
        for item in body:
            assert "name" in item
            assert "model" in item

    def test_post_valid_request(self, client):
        valid = _get_sensor_json()
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["name"] + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["name"] == "extra-sensor-1"
        assert body["model"] == "extrasensor"

    def test_wrong_mediatype(self, client):
        valid = _get_sensor_json()
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415

    def test_post_missing_field(self, client):
        valid = _get_sensor_json()
        valid.pop("model")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_post_name_conflict(self, client):
        valid = _get_sensor_json()
        valid["name"] = "test-sensor-1"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409


class TestSensorItem:

    RESOURCE_URL = "/api/sensors/test-sensor-1/"
    INVALID_URL = "/api/test/sensors/non-sensor-x/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert "name" in body
        assert "model" in body
        assert body["name"] == "test-sensor-1"
        assert body["model"] == "testsensor"

    def test_get_not_found(self, client):
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put_valid_request(self, client):
        valid = _get_sensor_json()
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204

    def test_wrong_mediatype(self, client):
        valid = _get_sensor_json()
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415

    def test_put_missing_field(self, client):
        valid = _get_sensor_json()
        valid.pop("model")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_put_name_conflict(self, client):
        valid = _get_sensor_json()
        valid["name"] = "test-sensor-2"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409


class TestMeasurementCollection:

    RESOURCE_URL = "/api/sensors/test-sensor-1/measurements/"

    def test_get(self, client):
        resp_page_1 = client.get(self.RESOURCE_URL)
        assert resp_page_1.status_code == 200
        body = json.loads(resp_page_1.data)
        assert "measurements" in body
        assert len(body["measurements"]) == 50
        p1_first = body["measurements"][0]
        assert "value" in p1_first
        assert "time" in p1_first
        first_timestamp = datetime.datetime.fromisoformat(p1_first["time"])
        resp_page_3 = client.get(self.RESOURCE_URL, query_string={"page": 2})
        body = json.loads(resp_page_3.data)
        assert len(body["measurements"]) == 25
        second_timestamp = datetime.datetime.fromisoformat(body["measurements"][0]["time"])
        assert second_timestamp == first_timestamp + datetime.timedelta(seconds=1000)
