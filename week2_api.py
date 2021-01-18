#imports
from flask import Flask
from flask_restful import Api, Resource,abort,request

#intializations
app=Flask(__name__)
api=Api(app)

#Validation Functions
def validate_req_body(body,request_name):
    if 'x' not in body or 'y' not in body:
        abort(400,status=False,message="variable missing in request")
    elif request_name=="Divide":
        try:
            x=int(body['x'])
            y=int(body['y'])
        except Exception as ex:
            abort(400,status=False,message="Invalid json x and y should be intergers")

        if y==0:
            abort(400,status=False,message="Division with 0 is always undefined")

#Route Resources
class Add(Resource):
    def post(self):
        req_json=request.get_json()
        validate_req_body(req_json,'Add')
        
        try:
            x=int(req_json['x'])
            y=int(req_json['y'])
        except Exception as ex:
            abort(400,status=False,message="Invalid json x and y should be intergers")
        
        return {
            "status":True,
            "data":x+y
        }

class Substract(Resource):
    def post(self):
        req_json=request.get_json()
        validate_req_body(req_json,'Substract')
        
        try:
            x=int(req_json['x'])
            y=int(req_json['y'])
        except Exception as ex:
            abort(400,status=False,message="Invalid json x and y should be intergers")
        
        return {
            "status":True,
            "data":x-y
        }

class Multiply(Resource):
    def post(self):
        req_json=request.get_json()
        validate_req_body(req_json,'Multiply')
        
        try:
            x=int(req_json['x'])
            y=int(req_json['y'])
        except Exception as ex:
            abort(400,status=False,message="Invalid json x and y should be intergers")
        
        return {
            "status":True,
            "data":x*y
        }

class Divide(Resource):
    def post(self):
        req_json=request.get_json()
        validate_req_body(req_json,'Divide')
        x=int(req_json['x'])
        y=int(req_json['y'])
        
        return {
            "status":True,
            "data":x/y
        }

#PATHS
api.add_resource(Add,'/add')
api.add_resource(Substract,'/substract')
api.add_resource(Multiply,'/multiply')
api.add_resource(Divide,'/divide')

if __name__=="__main__":
    app.run(debug=True)