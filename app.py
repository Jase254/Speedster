from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Welcome to Speedster!'


@app.route('/calories')
def calories():
    return 'You are fat!'


if __name__ == '__main__':
    app.run()
