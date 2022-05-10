from flask import Flask, render_template, request, redirect, send_file
import requests
import statistics as st
import csv
import os
import json
import time
import datetime
import matplotlib.pyplot as plt

flask_app = Flask(__name__)
mean_database = {}
summary_text = []
state = {1: '',
         2: '',
         3: '',
         4: '',
         5: ''}
delay = 5
heater_state = 'off'
humidifier_state = 'off'
decision_module_state = 'off'
plot_image = '/static/plot_image_default.jpg'


@flask_app.route('/', methods=['POST', 'GET'])
def index():
    global mean_database
    global summary_text
    if request.method == 'POST':
        summary_text = []
        try:
            mean_database = request.form.to_dict(flat=False)
            print(mean_database)
            for key in mean_database:
                mean_database[key] = [float(i) for i in mean_database[key]]
                value = "Średnia - " + str(key) + " przez " + str(delay) + "s: " + str(
                    round(st.mean(mean_database[key]), 2))
                summary_text.append(value)
            summary_text.sort()
            print(summary_text)
            return render_template('index.html', state=state, summary_text=summary_text, delay=delay,
                                   heater_state=heater_state, humidifier_state=humidifier_state,
                                   decision_module_state=decision_module_state, plot_image=plot_image)
        except:
            return 'There was an issue'
    else:
        return render_template('index.html', state=state, summary_text=summary_text, delay=delay,
                               heater_state=heater_state, humidifier_state=humidifier_state,
                               decision_module_state=decision_module_state, plot_image=plot_image)


@flask_app.route('/activate/<string:id>', methods=['POST', 'GET'])
def activation(id):
    try:
        activation_status = request.form['state' + id]
        if activation_status == 'on':
            try:
                requests.post("http://127.0.0.1:500" + str(id) + "/start", timeout=0.0000001)
                return redirect('/')
            except:
                return redirect('/')
        elif activation_status == 'off':
            requests.post("http://127.0.0.1:500" + str(id) + "/stop")
            return redirect('/')
    except:
        return redirect('/')


@flask_app.route('/method/<string:id>', methods=['POST', 'GET'])
def update_method(id):
    try:
        method_status = request.form['method' + id]
        requests.post("http://127.0.0.1:500" + str(id) + "/method/" + str(method_status))
        return redirect('/')
    except:
        return redirect('/')


@flask_app.route('/update/<string:id>', methods=['POST', 'GET'])
def update_int(id):
    try:
        interval = request.form['interval' + id]
        requests.post("http://127.0.0.1:500" + str(id) + "/update_int/" + str(interval))
        return redirect('/')
    except:
        return redirect('/')


@flask_app.route('/status/<int:id>', methods=['POST', 'GET'])
def update_status(id):
    try:
        global state
        status_data = request.form.to_dict(flat=True)
        state[id] = status_data
        print(status_data)
        return redirect('/')
    except:
        return redirect('/')


@flask_app.route('/delay', methods=['POST', 'GET'])
def update_delay():
    try:
        global delay
        delay = request.form['delay']
        requests.post("http://127.0.0.1:5000/update_delay/" + str(delay))
        return redirect('/')
    except:
        return redirect('/')


@flask_app.route('/decision_status', methods=['POST', 'GET'])
def update_decision_module_status():
    try:
        global decision_module_state
        decision_status = request.form['decision_status']
        requests.post("http://127.0.0.1:5011/status/" + str(decision_status))
        decision_module_state = decision_status
        return redirect('/')
    except:
        return redirect('/')


@flask_app.route('/heater', methods=['POST', 'GET'])
def update_heater():
    try:
        heater_status = request.form['heater']
        requests.post("http://127.0.0.1:5001/heater/" + str(heater_status))
        return redirect('/')
    except:
        return redirect('/')


@flask_app.route('/heater_status/<string:state>', methods=['POST', 'GET'])
def heater_state_update(state):
    global heater_state
    heater_state = state
    return redirect('/')


@flask_app.route('/humidifier', methods=['POST', 'GET'])
def update_humidifier():
    try:
        humidifier_status = request.form['humidifier']
        requests.post("http://127.0.0.1:5002/humidifier/" + str(humidifier_status))
        return redirect('/')
    except:
        return redirect('/')


@flask_app.route('/humidifier_status/<string:state>', methods=['POST', 'GET'])
def humidifier_state_update(state):
    global humidifier_state
    humidifier_state = state
    return redirect('/')


@flask_app.route('/download', methods=['POST', 'GET'])
def download():
    try:
        data = request.form
        save_method = data['save_method']
        date_from = time_translate(data['date_from'] + ' ' + data['time_from'])
        date_to = time_translate(data['date_to'] + ' ' + data['time_to'])
        source = data['source']
        plot_info = data['plot']
        return_value = requests.get('http://127.0.0.1:5000/database/' + source).text
        temp_database = json.loads(return_value)
        database = []
        path = str(os.getcwd() + "\\files")
        for j in temp_database[source]:
            if date_from > time_translate(j[1]):
                pass
            elif date_from <= time_translate(j[1]) <= date_to:
                database.append(j)
            else:
                break
        if plot_info == "on":
            plot_function(database, path)

        if save_method == 'csv':
            report_create_csv(path, database, source)
            return send_file(path + "\\report.csv", as_attachment=True)
        elif save_method == 'json':
            report_create_json(path, database, source)
            return send_file(path + "\\report.json", as_attachment=True)
        return redirect('/')
    except:
        return redirect('/')


def time_translate(data_time):
    return time.mktime(datetime.datetime.strptime(data_time, "%Y-%m-%d %H:%M").timetuple())


def report_create_csv(path, database, source):
    header = [source, "time", "value", "status"]
    print(path)
    with open(path + "\\report.csv", 'w', encoding='utf-8') as csvfile:
        csvwrite = csv.DictWriter(csvfile, header)
        csvwrite.writeheader()
        for i in database:
            write_data = {source: i[0],
                          'time': i[1],
                          'value': i[2],
                          'status': i[3]
                          }
            csvwrite.writerow(write_data)


def report_create_json(path, database, source):
    json_dict = {}
    for i in database:
        json_dict[source + "_" + i[0]] = {'time': i[1],
                                          'value': i[2],
                                          'status': i[3]
                                          }
    with open(path + "\\report.json", "w") as outfile:
        json.dump(json_dict, outfile)


def plot_function(database, path):
    global plot_image
    x_off = []
    y_off = []
    x_on = []
    y_on = []
    for j in database:
        if j[3] == 'on':
            x_on.append(int(j[0]))
            y_on.append(float(j[2]))
        x_off.append(int(j[0]))
        y_off.append(float(j[2]))

    plt.plot(x_off, y_off, '-', color='blue', label='Bez aktywatora')
    plt.plot(x_off[0], y_off[0], '-', color='red', label='Z aktywatorem')
    temp_x = []
    temp_y = []
    for i in range(1, len(x_on)):
        if int(x_on[i - 1]) == int(x_on[i]) - 1:
            temp_x.append(x_on[i])
            temp_y.append(y_on[i])
        else:
            plt.plot(temp_x, temp_y, '-', color='red')
            temp_x = []
            temp_y = []
    plt.plot(temp_x, temp_y, '-', color='red')
    plt.legend(framealpha=1, frameon=True)
    plt.savefig('static\\plot.jpg', bbox_inches='tight')
    plt.clf()
    plot_image = '/static/plot.jpg'


if __name__ == "__main__":
    flask_app.run(debug=True, port=4000)
