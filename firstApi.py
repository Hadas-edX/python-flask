from flask import Flask, jsonify, request
from flask_restful import Api, Resource
import functools
from pymongo import MongoClient

print = functools.partial(print, flush=True)

app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://flask-db:27017')
flask_db = client.flask
UserNum = flask_db['UserNum']

UserNum.insert_one({
    'num_of_users': 0
})


class Visit(Resource):
    def get(self):
        prev_num = UserNum.find({})[0]['num_of_users']
        new_num = prev_num + 1
        UserNum.update_one({}, {'$set': {'num_of_users': new_num}})
        return str('Hello, user ' + str(new_num))


def checkPostedData(postedData, functionName):
    if 'x' not in postedData or 'y' not in postedData:
        return 400
    if functionName == 'divide':
        if postedData['y'] == 0:
            return 401
    return 200


class Add(Resource):
    def post(self):
        postedData = request.get_json()
        status_code = checkPostedData(postedData, 'add')
        if status_code != 200:
            retMap = {
                'Message': 'An error happened',
                'Status Code': status_code
            }
            return jsonify(retMap)

        x = postedData['x']
        y = postedData['y']
        x = int(x)
        y = int(y)
        ret = x + y
        retMap = {
            'Message': ret,
            'Status Code': 200
        }
        return jsonify(retMap)


class Subtract(Resource):
    def post(self):
        postedData = request.get_json()
        status_code = checkPostedData(postedData, 'subtract')
        if status_code != 200:
            retMap = {
                'Message': 'An error happened',
                'Status Code': status_code
            }
            return jsonify(retMap)

        x = postedData['x']
        y = postedData['y']
        x = int(x)
        y = int(y)
        ret = x - y
        retMap = {
            'Message': ret,
            'Status Code': 200
        }
        return jsonify(retMap)


class Multiply(Resource):
    def post(self):
        postedData = request.get_json()
        status_code = checkPostedData(postedData, 'multiply')
        if status_code != 200:
            retMap = {
                'Message': 'An error happened',
                'Status Code': status_code
            }
            return jsonify(retMap)

        x = postedData['x']
        y = postedData['y']
        x = int(x)
        y = int(y)
        ret = x * y
        retMap = {
            'Message': ret,
            'Status Code': 200
        }
        return jsonify(retMap)


class Divide(Resource):
    def post(self):
        postedData = request.get_json()
        status_code = checkPostedData(postedData, 'divide')
        if status_code != 200:
            retMap = {
                'Message': 'An error happened',
                'Status Code': status_code
            }
            return jsonify(retMap)

        x = postedData['x']
        y = postedData['y']
        x = int(x)
        y = int(y)
        ret = x / y
        retMap = {
            'Message': ret,
            'Status Code': 200
        }
        return jsonify(retMap)


api.add_resource(Add, '/add')
api.add_resource(Subtract, '/subtract')
api.add_resource(Multiply, '/multiply')
api.add_resource(Divide, '/divide')
api.add_resource(Visit, '/hello')


@app.route('/')
def hello_world():
    return "Hello Guy!"


if __name__ == "__main__":
    app.run(debug=True)
