from flask import Flask, jsonify, request
from flask_restful import Api, Resource
import functools
from pymongo import MongoClient
from bcrypt import hashpw, gensalt, checkpw

print = functools.partial(print, flush=True)

app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://flask-db:27017')
database = client.sentences
users_collection = database['Users']


def hash_password(password):
    hashed_password = hashpw(password.encode('utf-8'), gensalt())
    return hashed_password


def verify_tokens(user_details):
    tokens_num = user_details['tokens']
    return tokens_num > 0


class Register(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData['username']
        password = postedData['password']
        hashed_password = hash_password(password)
        users_collection.insert_one({'username': username,
                                     'password': hashed_password,
                                     'sentences': [],
                                     'tokens': 10
                                     })

        response = jsonify({
            'Message': 'Registered Successfully!',
            'statusCode': 200})

        return response


class Store(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData['username']
        password = postedData['password']
        sentence = postedData['sentence']

        user_details = users_collection.find_one({'username': username})

        hashed_user_password = user_details['password']
        if checkpw(password.encode('utf-8'), hashed_user_password):

            enough_tokens = verify_tokens(user_details)
            if enough_tokens:

                user_sentences = user_details['sentences']
                user_tokens = user_details['tokens'] - 1
                user_sentences.append(sentence)
                users_collection.update_one(
                    {'username': username},
                    {
                        '$set': {
                            'sentences': user_sentences,
                            'tokens': user_tokens
                        }
                    }
                )

                response = jsonify({
                    'Message': 'Sentence saved successfully!',
                    'statusCode': 200})
            else:
                response = jsonify({
                    'Message': 'Not enough tokens',
                    'statusCode': 400})

        else:
            response = jsonify({
                'Message': 'Authentication failed',
                'statusCode': 401})

        return response


class Get(Resource):
    def get(self):
        postedData = request.get_json()
        username = postedData['username']
        password = postedData['password']

        user_details = users_collection.find_one({'username': username})

        hashed_user_password = user_details['password']
        if checkpw(password.encode('utf-8'), hashed_user_password):

            enough_tokens = verify_tokens(user_details)
            if enough_tokens:

                user_sentences = user_details['sentences']
                user_tokens = user_details['tokens'] - 1
                users_collection.update_one(
                    {'username': username},
                    {
                        '$set': {
                            'tokens': user_tokens
                        }
                    }
                )

                response = jsonify({
                    'Message': user_sentences,
                    'statusCode': 200})
            else:
                response = jsonify({
                    'Message': 'Not enough tokens',
                    'statusCode': 400})

        else:
            response = jsonify({
                'Message': 'Authentication failed',
                'statusCode': 401})

        return response


api.add_resource(Register, '/register')
api.add_resource(Store, '/store')
api.add_resource(Get, '/get')


if __name__ == "__main__":
    app.run(debug=True)
