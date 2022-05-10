import paho.mqtt.client as mqtt
from flask import Flask, request
import requests
import time
import json
import statistics as st

broker = "broker.hivemq.com"
client = mqtt.Client()
client.connect(broker)
flask_app = Flask(__name__)
adress_main = "http://127.0.0.1:4000/"
adress_decision_module = "http://127.0.0.1:5011/"
database = {'temperatura': [], 'wilgotnosc%': [], 'co2': [], 'gaz': [], 'czad': []}
mean_database = {}


def database_append(data):
    head = []
    for key in data:
        head.append(key)
    if head[0][3:] in mean_database:
        mean_database[head[0][3:]].append(float(data[head[2]]))
    else:
        mean_database[head[0][3:]] = [float(data[head[2]])]
    database[head[0][3:]].append([data[head[0]], data[head[1]], data[head[2]], data[head[3]]])
    requests.post(adress_decision_module, {head[0][3:]: float(data[head[2]])})


def on_connect(client, userdata, flags, rc):
    print("Połączono!")
    client.subscribe("254295_TEMP")


def on_message(client, userdata, message):
    data = json.loads(message.payload.decode('utf-8'))
    database_append(data)
    summary(delay)


def summary(delay):
    global start_time
    if time.time() - start_time >= delay:
        print(mean_database)
        requests.post(adress_main, mean_database)
        for key in mean_database:
            test = "Średnia - " + str(key) + " przez" + str(delay) + "s: " + str(st.mean(mean_database[key]))
            print(test)
        mean_database.clear()
        start_time = time.time()


@flask_app.route('/data', methods=['POST'])
def result():
    data = request.form.to_dict(flat=True)
    database_append(data)
    summary(delay)
    return ''


@flask_app.route('/update_delay/<int:up_delay>', methods=['GET', 'POST'])
def update_delay(up_delay):
    global delay
    delay = up_delay
    return ''


@flask_app.route('/database/<string:source>', methods=['GET', 'POST'])
def database_send(source):
    return {source: database[source]}


delay = 5
client.subscribe("254295_TEMP")
client.on_connect = on_connect
start_time = time.time()
while True:
    client.loop_start()
    client.on_message = on_message
    flask_app.run(debug=False, port=5000)
    client.loop_stop()
