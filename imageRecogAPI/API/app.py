#imports
from flask import Flask
from flask_restful import Api, Resource, abort, request
from pymongo import MongoClient
import bcrypt
import requests
import json
import subprocess

#intializations
app=Flask(__name__)
api=Api(app)
# db_client=MongoClient('mongodb://db:27017')
db_client=MongoClient('mongodb://localhost:27017')
db=db_client.ImageRecognizionDatabase
users_collection=db['Users']


#Validation Functions
def validate_user_req(body):
    if 'username' not in body or 'password' not in body:
        abort(400,status=False,message="username or password missing in request.")

def check_user_already_exists(username):
    count=users_collection.count_documents({"username":username})
    if count==0:
        return True
    return False

def verify_user(username,password):
    if check_user_already_exists(username):
        abort(400,status=False,message="user with this username dosen't exists.")
    user=users_collection.find({"username":username})[0]
    print(str(user))
    if user!=None:
        check_pass=bcrypt.checkpw(password.encode('utf8'),user['password'])
        if check_pass:
            return{'status':True,"token":user['token']}
        abort(400,status=False,message="Incorrect user password")
    abort(400,status=False,message="Incorrect username or password")

def validate_recognize_post_req(body):
    if 'username' not in body or 'password' not in body or 'image_url' not in body :
        abort(400,status=False,message="Request parameters are missing.")

#Route Resources Classes

class RegisterUser(Resource):
    def post(self):
        req_json=request.get_json()
        
        validate_user_req(req_json)

        username=str(req_json['username'])
        password=str(req_json['password'])
        
        if not check_user_already_exists(username):
            abort(400,status=False,message="This username is already assinged to another user please register with a different one.")

        hashed_pass=bcrypt.hashpw(password.encode('utf8'),bcrypt.gensalt())

        users_collection.insert({
            "username":username,
            "password":hashed_pass,
            "token":6
        })

        return{
            "status":True,
            "message":str("User created with username "+username+" with free 6 request tokens")
        },200

class Detect(Resource):
    
    def post(self):
        req_json=request.get_json()

        validate_recognize_post_req(req_json)

        username=str(req_json['username'])
        password=str(req_json['password'])
        image_url=str(req_json['image_url'])


        user_data=verify_user(username,password)

        if user_data['token']>0:
            
            #identify the image
            fetched_image=requests.get(image_url)
            res_json={}
            with open("temp.jpg","wb") as tem_image:
                tem_image.write(fetched_image.content)
                identification_process=subprocess.Popen('python classify_image.py --model_dir=. --image_file=./temp.jpg')
                identification_process.communicate()[0]
                identification_process.wait()
                with open("text.txt") as result_data:
                    res_json=json.load(result_data)

            users_collection.update({
                'username':username
            },{
                "$set":{
                    "token":user_data['token']-1
                }
            })

            return{
                "status":True,
                "message":"Image Identified sucessfully",
                "data":res_json
            },200
        
        abort(400,status=False,message="No more tokens left for request")

class BuyTokens(Resource):
    def post(self,no_of_tokens):
        print("ok")
        if no_of_tokens==3 or no_of_tokens==6 or no_of_tokens==10:
            
            req_json=request.get_json()
            
            validate_user_req(req_json)

            username=str(req_json['username'])
            password=str(req_json['password'])

            user_data=verify_user(username,password)

            users_collection.update({
                    'username':username
                },{
                    "$set":{
                        "token":user_data['token']+no_of_tokens
                    }
                })
            
            return{
                "status":True,
                "message":str(str(no_of_tokens)+" tokens added to your account"),
                "data":{
                    "username":username,
                    "tokens":user_data['token']+no_of_tokens
                }
            }
        
        abort(404)

#PATHS
api.add_resource(RegisterUser,'/register')
api.add_resource(Detect,'/recognize')
api.add_resource(BuyTokens,'/buytokens/<int:no_of_tokens>')

@app.route('/',methods=['GET'])
def Home():
    return """
        <h1>IMAGE RECOGNITION API</h1>
        <br>
        <h3>Available routes</h3>
        <p>/register&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;POST&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;to register a user</p>
        <p>/recognize&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;POST&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;to detect the similarity</p>
        <p>/buytokens/3&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;POST&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;to buy three tokens</p>
        <p>/buytokens/6&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;POST&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;to buy six tokens</p>
        <p>/buytokens/10&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;POST&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;to buy ten tokens</p>
    """

if __name__=="__main__":
    # app.run()
    app.run(host="0.0.0.0")
