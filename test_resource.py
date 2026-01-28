import json
import os
import pytest

from app import Sensor, app, db



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
        db.session.add(s)
    db.session.commit()

def _get_sensor_json(number=1):
    """
    Creates a valid sensor JSON object to be used for PUT and POST tests.
    """

    return {"name": "extra-sensor-{}".format(number), "model": "extrasensor"}


class TestSensorCollection(object):

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


class TestSensorItem(object):

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

