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
db=db_client.BankDatabase
users_collection=db['Users']

check_bank=users_collection.count_documents({"username":"BANK"})
if check_bank==0:
    bank_pass=bcrypt.hashpw("1234".encode('utf8'),bcrypt.gensalt())
    users_collection.insert({
        "username":"BANK",
        "password":bank_pass,
        "own_amount":0,
        "debt_amount":0
    })

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
    if user!=None:
        check_pass=bcrypt.checkpw(password.encode('utf8'),user['password'])
        if check_pass:
            return user
        abort(400,status=False,message="Incorrect user password")
    abort(400,status=False,message="Incorrect username or password")

def validate_post_req(body):
    if 'username' not in body or 'password' not in body or 'amount' not in body :
        abort(400,status=False,message="Request parameters are missing.")

def validate_transfer_req(body):
    if 'username' not in body or 'password' not in body or 'amount' not in body or "to_account" not in body :
        abort(400,status=False,message="Request parameters are missing.")

def update_own_amount(username,amount):
    users_collection.update({
        "username":username
    },{
        "$set":{
            "own_amount":amount
        }
    })

def update_debt_amount(username,amount):
    users_collection.update({
        "username":username
    },{
        "$set":{
            "debt_amount":amount
        }
    })

def get_available_cash(username,error_msg="user with this username dosen't exists."):
    if check_user_already_exists(username):
        abort(400,status=False,message=error_msg)
    user_data=users_collection.find({
        "username":username
    })[0]

    return user_data['own_amount']


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
            "own_amount":0,
            "debt_amount":0
        })

        return{
            "status":True,
            "message":str("User created with username "+username)
        },200

class AddMoney(Resource):
    def post(self):
        req_json=request.get_json()

        validate_post_req(req_json)

        username=str(req_json['username'])
        password=str(req_json['password'])
        try:
            amount=float(req_json['amount'])
        except Exception as e:
            abort(400,status=False,message="Amount should be an integer")

        user_data=verify_user(username,password)
        
        if amount>0:

            user_cash=user_data['own_amount']
            amount-=1
            bank_cash=get_available_cash("BANK")
            update_own_amount("BANK",bank_cash+1)
            update_own_amount(username,user_cash+amount)

            return{
                "status":True,
                "message":"Transaction Sucessfull",
                "data":{
                    "current_balance":user_cash+amount,
                    "amount_added":amount,
                    "transaction_fee":1
                }
            },200
        
        abort(400,status=False,message="Invalid amount was entered.")

class TransferMoney(Resource):
    def post(self):
        req_json=request.get_json()

        validate_transfer_req(req_json)

        username=str(req_json['username'])
        password=str(req_json['password'])
        try:
            amount=float(req_json['amount'])
        except Exception as e:
            abort(400,status=False,message="Amount should be an integer")
        to_account=str(req_json['to_account'])

        user_data=verify_user(username,password)
        
        if amount>0:
            user_cash=user_data['own_amount']
            to_account_cash=get_available_cash(to_account,"Account to transfer money dosn't exists.")
            bank_cash=get_available_cash("BANK")

            if user_cash>=amount:

                update_own_amount("BANK",bank_cash+1)
                update_own_amount(username,user_cash-amount)
                update_own_amount(to_account,to_account_cash+amount-1)

                return{
                    "status":True,
                    "message":"Transaction Sucessfull",
                    "data":{
                        "current_balance":user_cash-amount,
                        "amount_deducted":amount,
                        "transaction_fee":0
                    }
                },200
            
            abort(400,status=False,message="You don't have enough amount to transfer")

        abort(400,status=False,message="Invalid amount was entered.")


class CheckBalance(Resource):
    def get(self):
        req_json=request.get_json()

        validate_user_req(req_json)

        username=str(req_json['username'])
        password=str(req_json['password'])
        
        user_data=verify_user(username,password)
            
        return{
            "status":True,
            "message":"sucessfull",
            "data":{
                   "username":user_data['username'],
                   "current_balance":user_data['own_amount'],
                   "current_debt":user_data['debt_amount']
            }
        },200

class TakeLoan(Resource):
    def post(self):
        req_json=request.get_json()

        validate_post_req(req_json)

        username=str(req_json['username'])
        password=str(req_json['password'])
        amount=float(req_json['amount'])

        user_data=verify_user(username,password)

        if amount>0:
            user_cash=user_data['own_amount']
            user_debt=user_data['debt_amount']

            update_own_amount(username,user_cash+amount)
            update_debt_amount(username,user_debt+amount)

            return{
                "status":True,
                "message":"Loan sucessfull",
                "data":{
                    "current_balance":user_cash+amount,
                    "current_debt":user_debt+amount,
                }
            },200

        abort(400,status=False,message="Invalid amount was entered.")

class PayLoan(Resource):
    def post(self):
        req_json=request.get_json()

        validate_post_req(req_json)

        username=str(req_json['username'])
        password=str(req_json['password'])
        amount=float(req_json['amount'])

        user_data=verify_user(username,password)
            
        if amount>0:
            user_cash=user_data['own_amount']
            user_debt=user_data['debt_amount']

            if user_cash>=amount and amount<=user_debt:

                update_own_amount(username,user_cash-amount)
                update_debt_amount(username,user_debt-amount)

                return{
                    "status":True,
                    "message":"Loan paid sucessfully",
                    "data":{
                        "current_balance":user_cash-amount,
                        "current_debt":user_debt-amount,
                    }
                },200
            
            abort(400,status=False,message="You don't have enough amount to pay")

        abort(400,status=False,message="Invalid amount was entered.")

#PATHS
api.add_resource(RegisterUser,'/register')
api.add_resource(AddMoney,'/add')
api.add_resource(TransferMoney,'/transfer')
api.add_resource(CheckBalance,'/balance')
api.add_resource(TakeLoan,'/takeloan')
api.add_resource(PayLoan,'/payloan')

@app.route('/',methods=['GET'])
def Home():
    return """
        <h1>BANK API</h1>
        <br>
        <h3>Available routes</h3>
        <p>/register&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;POST&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;to register a user</p>
        <p>/add&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;POST&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;to add money to you bank account</p>
        <p>/transfer&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;POST&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;to transfer money from your bank account to another account</p>
        <p>/balance&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;GET&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;to check your current bank balance</p>
        <p>/takeloan&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;POST&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;to take a loan from the bank</p>
        <p>/payloan&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;POST&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;to pay the loan ammount to the bank</p>
    """

if __name__=="__main__":
    # app.run()
    app.run(host="0.0.0.0",debug=True)
