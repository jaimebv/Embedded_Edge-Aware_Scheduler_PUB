from flask import Flask, jsonify, request
import time

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello, from Server 1!'

@app.route('/server1', methods=['POST'])
def server_1():
    server_data=request.get_json()
    print (server_data)
    #time.sleep(2)

    return "hello from server 2"

app.run(host="0.0.0.0", port=6001, debug=True, use_reloader=True)