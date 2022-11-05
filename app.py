from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import functools
import spacy

print = functools.partial(print, flush=True)

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://flask-db:27017")
db = client .SimilarityDB
users = db["Users"]

nlp = spacy.load("./en_core_web_sm-3.0.0")


def userExists(username):
    if len(list(users.find({'username': username}))) == 0:
        return False
    return True


def verifyPassword(username, password):
    if not userExists(username):
        return False
    hashed = list(users.find({'username': username}))[0]['password']
    if bcrypt.checkpw(password.encode('utf8'), hashed):
        return True
    return False


def countTokens(username):
    tokensNumber = list(users.find({'username': username}))[0]['tokens']
    return tokensNumber


def detectSimilarity(text1, text2):
    doc1 = nlp(text1)
    doc2 = nlp(text2)
    return doc1.similarity(doc2)


class Register(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData['username']
        password = postedData['password']

        if userExists(username):
            retJson = {
                'status': 301,
                'msg': 'Invalid username'
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
        users.insert_one({
            'username': username,
            'password': hashed_pw,
            'tokens': 6})

        retJson = {
            'status': 200,
            'msg': 'You have successfully signed up'
        }

        return jsonify(retJson)


class Detect(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData['username']
        password = postedData['password']
        text1 = postedData['text1']
        text2 = postedData['text2']

        if not userExists(username):
            retJson = {
                'status': 301,
                'msg': "Invalid username"
            }
            return jsonify(retJson)

        if not verifyPassword(username, password):
            retJson = {
                'status': 302,
                'msg': 'Invalid password'
            }
            return jsonify(retJson)

        if countTokens(username) < 1:
            retJson = {
                'status': 303,
                'msg': 'Not enough tokens'
            }
            return jsonify(retJson)

        users.update_one({'username': username}, {'$inc': {'tokens': -1}})
        textSimilarity = detectSimilarity(text1, text2)

        retJson = {
            'status': 200,
            'msg': 'The similarity between the texts is ' + str(textSimilarity)
        }
        return jsonify(retJson)


class Refill(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData['username']
        admin_password = postedData['admin_password']
        refill_amount = postedData['refill_amount']

        if not userExists(username):
            retJson = {
                'status': 301,
                'msg': 'Invalid username'
            }
            return jsonify(retJson)

        if not verifyPassword('admin', admin_password):
            retJson = {
                'status': 304,
                'msg': 'Wrong admin password'
            }
            return jsonify(retJson)

        users.update_one({'username': username}, {'$set': {'tokens': refill_amount}})
        retJson = {
            'status': 200,
            'msg': 'Tokens refilled successfully for user ' + username
        }
        return jsonify(retJson)


api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')


if __name__ == "__main__":
    app.run(debug=True)
