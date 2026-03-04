from flask import Flask, jsonify, request
import time

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello fom SI Test Server!'

@app.route('/tm/si/latest_data', methods=['POST'])
def server_t1():
    server_data=request.get_json()
    print (server_data)
    #time.sleep(2)

    return "data received"

app.run(host="0.0.0.0", port=4999, debug=True, use_reloader=True)