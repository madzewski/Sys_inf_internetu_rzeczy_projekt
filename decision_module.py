import paho.mqtt.client as mqtt
from flask import Flask, request
import requests
import time
import json
import statistics as st

flask_app = Flask(__name__)
mean_database = {'temperatura': [], 'wilgotnosc%': []}
values = {'temperatura': 25, 'wilgotnosc%': 50}
alert_status = {'temperatura': 'off', 'wilgotnosc%': 'off'}
alarm_method = {'temperatura': 'http://127.0.0.1:5001/heater', 'wilgotnosc%': 'http://127.0.0.1:5002/humidifier'}
state = 'off'


def analyse(type):
    if len(mean_database[type]) < 5:
        pass
    else:
        if alert_status[type] == 'off':
            if st.mean(mean_database[type]) < values[type]:
                requests.post(alarm_method[type] + "/on")
                alert_status[type] = 'on'
        else:
            if st.mean(mean_database[type]) < values[type]*1.1:
                requests.post(alarm_method[type] + "/on")
            else:
                requests.post(alarm_method[type] + "/off")
                alert_status[type] = 'off'

        mean_database[type].pop(0)


@flask_app.route('/', methods=['GET', 'POST'])
def get_data():
    if state == 'on':
        data = request.form.to_dict(flat=True)
        for i in data:
            if i in mean_database:
                mean_database[i].append(float(data[i]))
                print(mean_database)
                analyse(i)
    return ''


@flask_app.route('/status/<string:status>', methods=['GET', 'POST'])
def update_status(status):
    global state
    global mean_database
    database = {'temperatura': [], 'wilgotnosc%': []}
    state = status
    return ''


if __name__ == "__main__":
    flask_app.run(debug=True, port=5011)
