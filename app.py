from flask import Flask, render_template, session, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, StringField
from wtforms.validators import data_required
from flask_moment import Moment
from flask_googlemaps import GoogleMaps, Map
from flask_bower import Bower

app = Flask(__name__)

app.config['SECRET_KEY'] = "mysecrebotkey"
app.config['GOOGLEMAPS_KEY'] = 'AIzaSyBAecs30c9qmrQaHzG8rskQdyJvmDYJh4s'

GoogleMaps(app)
moment = Moment(app)
Bower(app)


@app.route('/')
def hello_world():
    return render_template('index.html', speed=80, acceleration=60, velocity=20)


@app.route('/metrics')
def calories():
    return render_template('graphs.html')


if __name__ == '__main__':
    app.run()
