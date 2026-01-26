import datetime
import importlib
import random
import os
flask_app = os.environ.get("FLASK_APP")
app = importlib.import_module(flask_app)


with app.app.app_context():

    app.db.create_all()

    for idx, letter in enumerate("ABC", start=1):
        loc = app.Location(
            name=f"Location-{letter}",
            latitude=round(random.random() * 100, 2),
            longitude=round(random.random() * 100, 2),
            altitude=round(random.random() * 100, 2),
        )
        sensor = app.Sensor(
            name=f"Sensor-{idx}",
            model="test-sensor",
        )
        sensor.location = loc

        now = datetime.datetime.now()
        interval = datetime.timedelta(seconds=10)
        for i in range(1000):
            meas = app.Measurement(
                value=round(random.random() * 100, 2),
                time=now
            )
            now += interval
            sensor.measurements.append(meas)

        app.db.session.add(sensor)

    app.db.session.commit()

