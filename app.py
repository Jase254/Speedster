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
import random
from multiprocessing import Process
import time
from geopy import distance

app = Flask(__name__)

app.config['SECRET_KEY'] = "mysecrebotkey"
app.config['GOOGLEMAPS_KEY'] = 'AIzaSyBAecs30c9qmrQaHzG8rskQdyJvmDYJh4s'

uri = "mongodb://speedstermongo:hihfszN56ne6U4ht4ocN0PKfiDNsOBYNBqbwW5yvVdy2psXmjrwyG7WtSVOTfVzyn18sCI32Na3oF2RCgbK2AA==@speedstermongo.documents.azure.com:10255/?ssl=true&replicaSet=globaldb"
client = MongoClient(uri, ssl=True, ssl_cert_reqs=ssl.CERT_NONE)

GoogleMaps(app)
moment = Moment(app)
Bower(app)

DB = None
lastSequence = None
last_valid_sequence = None


def connect_mongo():
    global DB
    uri = "mongodb://speedstermongo:hihfszN56ne6U4ht4ocN0PKfiDNsOBYNBqbwW5yvVdy2psXmjrwyG7WtSVOTfVzyn18sCI32Na3oF2RCgbK2AA==@speedstermongo.documents.azure.com:10255/?ssl=true&replicaSet=globaldb"
    client = MongoClient(uri, ssl=True, ssl_cert_reqs=ssl.CERT_NONE)
    DB = client["Speedster_DB"]
    print("DB Connected")


def mongo_insert(data):
    global DB
    for entries in data:
        DB.Speedster_Data.update(
            entries,
            {"$set": entries},
            upsert=True)


# Use "@latest" for most current
# Use "-1" for all
def get_iot_message(offset):
    global lastSequence
    global last_valid_sequence

    CONSUMER_GROUP = "$default"
    print(lastSequence)
    print(last_valid_sequence)
    print(offset)

    if lastSequence is None:
        OFFSET = Offset(offset)
    else:
        OFFSET = Offset(lastSequence)
    PARTITION = "0"
    messages = []

    connection_str = "Endpoint=sb://speedster.servicebus.windows.net/;SharedAccessKeyName=iothubroutes_SpeedsterHub;SharedAccessKey=nEErnnHfOnkGdyrKq7VUg91IWNNNyUt3JUE1t2ygqU8=;EntityPath=clean"

    total = 0
    client = EventHubClient.from_connection_string(connection_str, debug=False)
    try:
        receiver = client.add_receiver(CONSUMER_GROUP, PARTITION, prefetch=300, offset=OFFSET)
        client.run()
        batched_events = receiver.receive(max_batch_size=300, timeout=15)
        for event_data in batched_events:
            total += 1
            offset = event_data.offset.value
            sn = event_data.sequence_number
            message = event_data.body_as_json()
            message["time"] = event_data.enqueued_time
            message['offset'] = offset
            message['sequence'] = sn
            message['fixed'] = bool(message["fix"])
            lastSequence = sn
            if message["fixed"]:
                last_valid_sequence = sn
                messages.append(message)

    except KeyboardInterrupt:
        pass
    finally:
        client.stop()

    return messages


def latest_record(years, month, day):
    global last_valid_sequence
    global DB
    message = DB.Speedster_Data.find_one({"sequence": last_valid_sequence})
    beginning = datetime.datetime(years, month, day) + datetime.timedelta(hours=8)
    end = beginning + datetime.timedelta(days=1)

    if message["time"] > beginning and message["time"] < end:
        return message
    else:
        return None


def random_distance():
    return random.randint(0, 6)


def get_distance_travelled(year, month, day):
    global DB
    distance_total = 0
    beginning = datetime.datetime(year,month, day) + datetime.timedelta(hours=8)
    end = beginning + datetime.timedelta(days=1)
    entries = DB.Speedster_Data.find({"time": {"$gte": beginning, "$lte": end}})
    if entries.count() > 2:
        start = (entries[0]["latitude"], entries[0]["longitude"])
        for entry in entries[1:]:
            end = (entry["latitude"], entry["longitude"])
            distance_total += distance.great_circle(start, end).miles
            start = end

    return distance_total

@app.route('/')
def hello_world():
    connect_mongo()
    messages = get_iot_message('-1')
    mongo_insert(messages)
    date = datetime.datetime.now()
    current = latest_record(date.year, date.month, date.day)
    if current is not None:
        total_distance = get_distance_travelled(date.year, date.month, date.day)
        lat = current['latitude']
        long = current['longitude']
        calories = current['calories']
        altitude = current['altitude']
        velocity = current['velocity'] * 2.23694
        today = True
    else:
        total_distance = 0
        lat = 0
        long = 0
        calories = 0
        altitude = 0
        velocity = 0
        today = False

    return render_template('index.html', today=today, total_distance=total_distance, distance=4, speed=velocity, calories=calories, lat=lat, long=long)


@app.route('/updatedb')
def update_db():
    connect_mongo()
    messages = get_iot_message('-1')
    mongo_insert(messages)

    return "{} Records Added to the DB".format(len(messages))


if __name__ == '__main__':
    app.run()
