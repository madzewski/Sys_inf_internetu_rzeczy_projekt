import csv
import paho.mqtt.client as mqtt
from flask import Flask
import json
import requests
import time
import os
import math

flask_app = Flask(__name__)
current_row = 0


def sending_mqtt(data):
    data['status'] = heater_status
    client.publish('254295_TEMP', json.dumps(data))
    print(data)


def sending_http(data):
    data['status'] = heater_status
    requests.post(adress + 'data', data)
    print(data)


def sending_status(info):
    data = {}
    if info[0] == False:
        data['state'] = 'ON'
    else:
        data['state'] = 'OFF'
    data['method'] = str(info[1])
    data['interval'] = str(info[2])
    requests.post("http://127.0.0.1:4000/status/1", data)


def sending_heater_status(status):
    requests.post("http://127.0.0.1:4000/heater_status/"+status)


def heater_influence(data, n):
    if math.log(n, 20) < 1.5:
        r = float(data) * math.log(n, 20)
    else:
        r = float(data) * 1.5
    return round(r, 2)


@flask_app.route('/start', methods=['GET', 'POST'])
def sending():
    global stop
    global current_row
    temp_row = 0
    stop = False
    heater_min_count = 20
    csvfile = open(path, 'r', encoding='utf-8')
    csvread = csv.DictReader(csvfile)
    headers = csvread.fieldnames
    sending_status([stop, method, interval[1]])
    for row in csvread:
        if stop == False:
            if current_row == 0:
                if interval[0] == interval[1]:
                    data = {}
                    for n in headers:
                        data[n] = row[n]
                    if heater_status == 'on':
                        data['temp'] = heater_influence(data['temp'], heater_min_count)
                        sending_heater_status('on')
                        heater_min_count += 1
                    else:
                        if heater_min_count == 20:
                            sending_heater_status('off')
                        elif 90 >= heater_min_count >= 20:
                            heater_min_count -= 1
                            data['temp'] = heater_influence(data['temp'], heater_min_count)
                            sending_heater_status('off')
                        elif heater_min_count < 20:
                            heater_min_count = 20
                            sending_heater_status('off')
                        else:
                            heater_min_count = 90
                            sending_heater_status('off')

                    if method == 'mqtt':
                        sending_mqtt(data)
                    elif method == 'http':
                        sending_http(data)
                    interval[0] = 1
                else:
                    interval[0] += 1
                temp_row += 1
                time.sleep(1)
            else:
                temp_row += 1
                current_row -= 1
        else:
            current_row = temp_row
    return "Koniec"


@flask_app.route('/stop', methods=['GET', 'POST'])
def stop_sending():
    global stop
    stop = True
    sending_status([stop, method, interval[1]])
    return "STOP"


@flask_app.route('/update_int/<int:up_interval>', methods=['GET', 'POST'])
def update_int(up_interval):
    global interval
    interval[0] = 1
    interval[1] = up_interval
    sending_status([stop, method, interval[1]])
    return ""


@flask_app.route('/method/<string:meth>', methods=['GET', 'POST'])
def update_method(meth):
    global method
    method = meth
    sending_status([stop, method, interval[1]])
    return ""


@flask_app.route('/heater/<string:status>', methods=['GET', 'POST'])
def heater(status):
    global heater_status
    heater_status = status
    return ''


broker = "broker.hivemq.com"
client = mqtt.Client()
client.connect(broker)
adress = "http://127.0.0.1:5000/"
adress_decision_module = "http://127.0.0.1:5011/"
filename = "test1.csv"
path = str(os.getcwd() + "\\dane\\" + filename)
interval = [1, 1]
method = 'http'
stop = True
heater_status = 'off'
flask_app.run(debug=False, port=5001)
