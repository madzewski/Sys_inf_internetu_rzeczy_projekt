import csv
import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request
import json
import requests
import time
import os

flask_app = Flask(__name__)
current_row = 0


def sending_mqtt(data):
    data['status'] = influencer
    client.publish('254295_TEMP', json.dumps(data))
    print(data)


def sending_http(data):
    data['status'] = influencer
    requests.post(adress + 'data', data)
    print(data)


def sending_status(info):
    data={}
    if info[0] == False:
        data['state']='ON'
    else:
        data['state']='OFF'
    data['method'] = str(info[1])
    data['interval'] = str(info[2])
    requests.post("http://127.0.0.1:4000/status/4", data)


@flask_app.route('/start', methods=['GET', 'POST'])
def sending():
    global stop
    global current_row
    temp_row = 0
    stop = False
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
                    print(data)
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


broker = "broker.hivemq.com"
client = mqtt.Client()
client.connect(broker)
adress = "http://127.0.0.1:5000/"
filename = "test4.csv"
path = str(os.getcwd() + "\\dane\\" + filename)
interval = [1, 1]
method = 'http'
stop = True
influencer = 'off'
flask_app.run(debug=False, port=5004)
