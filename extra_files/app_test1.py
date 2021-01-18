from flask import Flask,jsonify
from flask.globals import request

app=Flask(__name__)

@app.route('/')
def Hello_world():
    return "Hello World"

@app.route('/add',methods=['POST'])
def add():
    request_json=request.get_json()
    if "x" not in request_json or "y" not in request_json:
        return {"status":False,"message":"variables missing in request"},400
    return {
        "status":True,
        "data":request_json['x']+request_json['y']
    },200

@app.route('/json')
def json():
    c={
        "hello":"There"
    }
    return c

if __name__=="__main__":
    app.run(debug=True)