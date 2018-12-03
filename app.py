from flask import Flask, render_template, session, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, StringField
from wtforms.validators import data_required
from flask_moment import Moment
from flask_googlemaps import GoogleMaps, Map
from flask_bower import Bower
import ssl
from pymongo import MongoClient
from azure.eventhub import EventHubClient, Receiver, Offset
import json
import datetime
from flask import jsonify

app = Flask(__name__)

app.config['SECRET_KEY'] = "mysecrebotkey"
app.config['GOOGLEMAPS_KEY'] = 'AIzaSyBAecs30c9qmrQaHzG8rskQdyJvmDYJh4s'

uri = "mongodb://speedstermongo:hihfszN56ne6U4ht4ocN0PKfiDNsOBYNBqbwW5yvVdy2psXmjrwyG7WtSVOTfVzyn18sCI32Na3oF2RCgbK2AA==@speedstermongo.documents.azure.com:10255/?ssl=true&replicaSet=globaldb"
client = MongoClient(uri, ssl=True, ssl_cert_reqs=ssl.CERT_NONE)

GoogleMaps(app)
moment = Moment(app)
Bower(app)

DB = None


def connect_mongo():
    global DB
    uri = "mongodb://speedstermongo:hihfszN56ne6U4ht4ocN0PKfiDNsOBYNBqbwW5yvVdy2psXmjrwyG7WtSVOTfVzyn18sCI32Na3oF2RCgbK2AA==@speedstermongo.documents.azure.com:10255/?ssl=true&replicaSet=globaldb"
    client = MongoClient(uri, ssl=True, ssl_cert_reqs=ssl.CERT_NONE)
    DB = client["Speedster_DB"]
    print("DB Connected")


def mongo_insert(data):
    global DB
    DB.Speedster_Data.insert_one(data)


# Use "@latest" for most current
# Use "-1" for all
def get_iot_message(offset):
    CONSUMER_GROUP = "$default"
    OFFSET = Offset(offset)
    PARTITION = "0"
    messages = []

    connection_str = "Endpoint=sb://speedster.servicebus.windows.net/;SharedAccessKeyName=iothubroutes_SpeedsterHub;SharedAccessKey=RbF5Vf4Rm4DumTY0LAHwdYfaZPafAwo/yVWFdECH08k=;EntityPath=telemetry"

    total = 0
    client = EventHubClient.from_connection_string(connection_str, debug=False)
    try:
        receiver = client.add_receiver(CONSUMER_GROUP, PARTITION, prefetch=300, offset=OFFSET)
        client.run()
        batched_events = receiver.receive(max_batch_size=None)
        for event_data in batched_events:
            total += 1
            offset = event_data.offset.value
            sn = event_data.sequence_number
            message = event_data.body_as_json()
            message["time"] = datetime.datetime.utcnow()
            message['offset'] = offset
            message['sequence'] = sn
            messages.append(message)
            print(message)

    except KeyboardInterrupt:
        pass
    finally:
        client.stop()

    return messages


@app.route('/')
def hello_world():
    connect_mongo()
    messages = get_iot_message('-1')
    print(messages[0])
    current = messages[0]
    mongo_insert(messages[0])
    lat = current['latitude']
    long = current['longitude']
    calories = current['calories']
    altitude = current['altitude']
    velocity = current['velocity']
    date = datetime.date.today()
    print(date.isoformat())

    return render_template('index.html', date=date.isoformat(), distance=4, speed=15, calories=3, lat=33.6461, long=-117.8427)


@app.route('/updatedb')
def update_db():
    connect_mongo()
    messages = get_iot_message('-1')
    print(messages[0])
    mongo_insert(messages[0])

    return


if __name__ == '__main__':
    app.run()
