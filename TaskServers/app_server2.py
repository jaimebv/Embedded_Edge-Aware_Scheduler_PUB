from flask import Flask, jsonify, request
import time

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello, from Server 2!'

@app.route('/server2', methods=['POST'])
def server_2():
    server_data=request.get_json()
    print (server_data)
    #time.sleep(2)

    return "hello from server 2"

app.run(host="0.0.0.0", port=6002, debug=True, use_reloader=True)