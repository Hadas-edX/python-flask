from flask import Flask, jsonify, request
from flask_restful import Api, Resource
import functools
from pymongo import MongoClient
from bcrypt import hashpw, gensalt, checkpw

print = functools.partial(print, flush=True)

app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://flask-db:27017')
database = client.bankApi
users_collection = database['Users']


def hash_password(password):
    hashed_password = hashpw(password.encode('utf-8'), gensalt())
    return hashed_password


def user_exists(username):
    if len(list(users_collection.find({'username': username}))) == 0:
        return False
    return True


def verify_password(username, password):
    if not user_exists:
        return False
    hashed_pw = users_collection.find_one({'username': username})['password']

    if checkpw(password.encode('utf-8'), hashed_pw):
        return True
    return False


def cash_with_user(username):
    cash = users_collection.find_one({'username': username})['Own']
    return cash


def debt_with_user(username):
    debt = users_collection.find_one({'username': username})['Debt']
    return debt


def generate_return_dict(status, msg):
    retJson = {
        'statusCode': status,
        'Message': msg
    }
    return retJson


def verify_credentials(username, password):
    if not user_exists(username):
        return generate_return_dict(301, 'Invalid Username'), True

    correct_pw = verify_password(username, password)
    if not correct_pw:
        return generate_return_dict(302, 'Incorrect Password'), True
    return None, False


def update_account(username, balance):
    users_collection.update_one({
        'username': username
    }, {
        '$set': {
            'Own': balance
        }})


def update_debt(username, balance):
    users_collection.update_one({
        'username': username
    }, {
        '$set': {
            'Debt': balance
        }})


class Register(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData['username']
        password = postedData['password']
        if user_exists(username):
            retJson = {
                'statusCode': 301,
                'Message': 'Invalid Username'
            }
            return jsonify(retJson)
        hashed_password = hash_password(password)
        users_collection.insert_one({'username': username,
                                     'password': hashed_password,
                                     'Own': 0,
                                     'Debt': 0
                                     })

        response = jsonify({
            'Message': 'Registered Successfully!',
            'statusCode': 200})

        return response


class Add(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData['username']
        password = postedData['password']
        amount = postedData['amount']
        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)

        if amount <= 0:
            return jsonify(generate_return_dict(304, 'Money amount entered must be greater than 0'))

        cash = cash_with_user(username)
        amount -= 1
        bank_cash = cash_with_user('bank')
        update_account('bank', bank_cash+1)
        update_account(username, cash+amount)

        return jsonify(generate_return_dict(200, 'Money added successfully'))


class Tranfer(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData['username']
        password = postedData['password']
        to = postedData['to']
        money = postedData['amount']

        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)

        cash = cash_with_user(username)

        if cash <= 0:
            return jsonify(generate_return_dict(304, 'Out of money'))

        if not user_exists(to):
            return jsonify(generate_return_dict(301, 'Receiver username is invalid'))

        cash_from = cash_with_user(username)
        cash_to = cash_with_user(to)
        bank_cash = cash_with_user('bank')

        update_account('bank', bank_cash+1)
        update_account(to, cash_to + money - 1)
        update_account(username, cash_from - money)

        return jsonify(generate_return_dict(200, 'Amount transferred successfully'))


class Balance(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData['username']
        password = postedData['password']

        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)

        retJson = users_collection.find_one({
            'username': username,
        }, {
            'password': 0,
            '_id': 0
        })

        return jsonify(retJson)


class TakeLoan(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData['username']
        password = postedData['password']
        money = postedData['amount']

        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)

        cash = cash_with_user(username)
        debt = debt_with_user(username)

        update_account(username, cash+money)
        update_debt(username, debt+money)

        return jsonify(generate_return_dict(200, 'Loan taken successfully'))


class PayLoan(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData['username']
        password = postedData['password']
        money = postedData['amount']

        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)

        cash = cash_with_user(username)
        if cash < money:
            return jsonify(generate_return_dict(303, 'Not enough cash in your account'))

        debt = debt_with_user(username)

        update_account(username, cash-money)
        update_debt(username, debt-money)

        return jsonify(generate_return_dict(200, 'Loan paid successfully'))


api.add_resource(Register, '/register')
api.add_resource(Add, '/add')
api.add_resource(Tranfer, '/transfer')
api.add_resource(Balance, '/balance')
api.add_resource(TakeLoan, '/takeloan')
api.add_resource(PayLoan, '/payloan')


if __name__ == "__main__":
    app.run(debug=True)
