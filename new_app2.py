import csv
import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request
import json
import requests
import time
import os
import math


flask_app = Flask(__name__)
current_row = 0


def sending_mqtt(data):
    data['status'] = humidifier_status
    client.publish('254295_TEMP', json.dumps(data))
    print(data)


def sending_http(data):
    data['status'] = humidifier_status
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
    requests.post("http://127.0.0.1:4000/status/2", data)


def sending_humidifier_status(status):
    requests.post("http://127.0.0.1:4000/humidifier_status/"+status)


def humidifier_influence(data, n):
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
    humidifier_min_count = 20
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
                    if humidifier_status == 'on':
                        data['humi%'] = humidifier_influence(data['humi%'], humidifier_min_count)
                        sending_humidifier_status('on')
                        humidifier_min_count += 1
                    else:
                        if humidifier_min_count == 20:
                            sending_humidifier_status('off')
                        elif 90 >= humidifier_min_count >= 20:
                            humidifier_min_count -= 1
                            data['humi%'] = humidifier_influence(data['humi%'], humidifier_min_count)
                            sending_humidifier_status('off')
                        elif humidifier_min_count < 20:
                            humidifier_min_count = 20
                            sending_humidifier_status('off')
                        else:
                            humidifier_min_count = 90
                            sending_humidifier_status('off')
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


@flask_app.route('/humidifier/<string:status>', methods=['GET', 'POST'])
def humidifier(status):
    global humidifier_status
    humidifier_status = status
    return ''


broker = "broker.hivemq.com"
client = mqtt.Client()
client.connect(broker)
adress = "http://127.0.0.1:5000/"
filename = "test2.csv"
path = str(os.getcwd() + "\\dane\\" + filename)
interval = [1, 1]
method = 'http'
stop = True
humidifier_status = 'off'
flask_app.run(debug=False, port=5002)
