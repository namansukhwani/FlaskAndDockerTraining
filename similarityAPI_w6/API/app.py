#imports
from flask import Flask
from flask_restful import Api, Resource, abort, request
from pymongo import MongoClient
import bcrypt

#intializations
app=Flask(__name__)
api=Api(app)
db_client=MongoClient('mongodb://db:27017')
# db_client=MongoClient('mongodb://localhost:27017')
db=db_client.SentenceDatabase
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
    user=users_collection.find({"username":username})[0]
    print(str(user))
    if user!=None:
        check_pass=bcrypt.checkpw(password.encode('utf8'),user['password'])
        if check_pass:
            return{'status':True,"token":user['token']}
        abort(400,status=False,message="Incorrect user password")
    abort(400,status=False,message="Incorrect username or password")

def validate_sentence_post_req(body):
    if 'username' not in body or 'password' not in body or 'sentence' not in body:
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
            "sentence":"",
            "token":6
        })

        return{
            "status":True,
            "message":str("User created with username "+username+" with free 6 request tokens")
        },200

class Sentences(Resource):
    def get(self):
        req_json=request.get_json()
        
        validate_user_req(req_json)

        username=str(req_json['username'])
        password=str(req_json['password'])

        user_data=verify_user(username,password)
        

        if user_data['token']>0:
            sentence=users_collection.find({"username":username})[0]['sentence']
            
            users_collection.update({
                'username':username
            },{
                "$set":{
                    "token":user_data['token']-1
                }
            })


            return{
                "status":True,
                "message":"Sentence fetched sucessfully",
                "data":str(sentence)
            }

        abort(400,status=False,message="No more tokens left for request")
    
    def post(self):
        req_json=request.get_json()

        validate_sentence_post_req(req_json)

        username=str(req_json['username'])
        password=str(req_json['password'])
        sentence=str(req_json['sentence'])

        user_data=verify_user(username,password)

        if user_data['token']>0:
            users_collection.update({
                'username':username
            },{
                "$set":{
                    "sentence":sentence,
                    "token":user_data['token']-1
                }
            })

            return{
                "status":True,
                "message":"Sentence added sucessfully",
                "data":sentence
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
api.add_resource(Sentences,'/sentence')
api.add_resource(BuyTokens,'/buytokens/<int:no_of_tokens>')

@app.route('/',methods=['GET'])
def Home():
    return """
        <h1>SENTENCE API</h1>
        <br>
        <h3>Available routes</h3>
        <p>/register      &nbsp;&nbsp;&nbsp;&nbsp;       POST      &nbsp;&nbsp;&nbsp;&nbsp;   to register a user</p>
        <p>/sentence      &nbsp;&nbsp;&nbsp;&nbsp;       GET,POST  &nbsp;&nbsp;&nbsp;&nbsp;   to retrive and post sentence</p>
        <p>/buytokens/3   &nbsp;&nbsp;&nbsp;&nbsp;       POST    &nbsp;&nbsp;&nbsp;&nbsp;    to buy three tokens</p>
        <p>/buytokens/6    &nbsp;&nbsp;&nbsp;&nbsp;      POST     &nbsp;&nbsp;&nbsp;&nbsp;    to buy six tokens</p>
        <p>/buytokens/10   &nbsp;&nbsp;&nbsp;&nbsp;       POST   &nbsp;&nbsp;&nbsp;&nbsp;      to buy ten tokens</p>
    """

if __name__=="__main__":
    # app.run()
    app.run(host="0.0.0.0")
